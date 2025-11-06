# CliSelf/modules/forward/multi_forward_manager.py  (optimized for low CPU)
# ---------------------------------------------------------------------------------
# اهداف بهینه‌سازی بدون تغییر کارکرد:
# - حذف busy-wait؛ هر حلقهٔ دائمی حتماً sleep معنی‌دار دارد
# - backoff نمایی برای خطاها/FloodWait با jitter
# - تاخیرهای قابل‌تنظیم: delay ارسال، وقفه بین دورها (_cycle_delay)
# - توقف تمیز: cancel تسک‌ها و پایان graceful
# - نرخ‌دهی داخلی (rate limit) برای مقصدها در صورت نیاز
# - پایداری نوع: src/dst می‌توانند int یا str باشند
# - گزارش exception تسک
# ---------------------------------------------------------------------------------

import asyncio
import random
from typing import Iterable, List, Optional, Sequence, Tuple, Union

from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

try:
    from ...core.logger import get_logger  # type: ignore
    logger = get_logger("multi_forward")
except Exception:
    import logging
    logger = logging.getLogger("multi_forward")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)


Ident = Union[int, str]
Item = Tuple[Ident, Optional[int], Optional[int]]  # (source, start_id, end_id)


class MultiForwarder:
    """
    MultiForwarder
    ---------------
    یک فوروارد‌کنندهٔ چند-منظوره که آیتم‌های (src→dst) را پشت‌سرهم می‌فرستد.
    - `items`: فهرست (source, start_id, end_id) یا مشابه
    - `targets`: فهرست مقصدها (chat_id/username/'me' یا int)
    - `delay`: تاخیر بین چانک‌ها (ثانیه)
    - `_cycle_delay`: وقفه بین دورهای کامل
    """

    # پیش‌فرض‌های محافظه‌کارانه برای هاست اشتراکی
    _CHUNK_SIZE_DEFAULT: int = 40
    _DELAY_DEFAULT: float = 1.5
    _CYCLE_DELAY_DEFAULT: float = 3.0
    _PAGE_SIZE_DEFAULT: int = 100
    _BACKOFF_BASE: float = 1.0
    _BACKOFF_CAP: float = 60.0
    _JITTER: float = 0.25

    def __init__(self, client: Client):
        self.client = client
        self.items: List[Item] = []
        self.targets: List[Ident] = []
        self.delay: float = self._DELAY_DEFAULT
        self._cycle_delay: float = self._CYCLE_DELAY_DEFAULT
        self._task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        logger.info("MultiForwarder initialized (optimized).")

    # -------------------------------
    # تنظیم و وضعیت
    # -------------------------------
    def set_items(self, items: Sequence[Item]) -> None:
        # کپی امن
        self.items = [(src, start, end) for (src, start, end) in items]

    def set_targets(self, targets: Iterable[Ident]) -> None:
        self.targets = [t for t in targets]

    def set_delay(self, seconds: float) -> None:
        self.delay = max(0.5, float(seconds))

    def set_cycle_delay(self, seconds: float) -> None:
        self._cycle_delay = max(1.0, float(seconds))

    def status(self) -> str:
        return (
            "📊 **وضعیت MultiForwarder**\n"
            f"🔹 آیتم‌ها: {len(self.items)}\n"
            f"🔹 تارگت‌ها: {len(self.targets)}\n"
            f"⏱ فاصله ارسال: {self.delay} ثانیه\n"
            f"🔁 فاصله بین دورها: {self._cycle_delay} ثانیه\n"
            f"🚦 فعال: {'✅' if self.is_running else '❌'}"
        )

    # -------------------------------
    # کمکی‌ها
    # -------------------------------
    async def _resolve(self, ident: Optional[Ident]) -> Optional[Union[int, str]]:
        """رزولوشن مقصد/مبدأ؛ ورودی می‌تواند int یا str باشد."""
        if ident is None:
            return None

        # اگر int خالصه، همون رو برگردون (فرض chat_id/user_id)
        if isinstance(ident, int):
            return ident

        # از اینجا به بعد: str
        s = ident.strip()
        if not s:
            return None

        if s.lower() == "me":
            return "me"

        # اگر رشته‌ای از ارقام (با یا بدون -) بود: سعی کن به int تبدیل کنی
        if s.lstrip("-").isdigit():
            try:
                num = int(s)
                # چکِ وجود چت/کاربر (اختیاری ولی بهتر)
                try:
                    return (await self.client.get_chat(num)).id
                except Exception:
                    return (await self.client.get_users(num)).id
            except Exception:
                # اگر تبدیل نشد، ادامه بده با resolve یوزرنیم
                pass

        # تلاش برای یوزرنیم/لینک
        try:
            return (await self.client.get_chat(s)).id
        except Exception:
            try:
                return (await self.client.get_users(s)).id
            except Exception:
                return None

    async def _iter_history_ids(self, chat_id, page_size: int):
        """
        در Pyrogram v2، get_chat_history یک async generator است.
        این تابع هر بار یک «صفحه» از شناسه پیام‌ها برمی‌گرداند.
        """
        offset_id = 0
        while True:
            batch = []
            # صفحه‌ی بعدی را با offset_id و limit می‌خوانیم
            async for msg in self.client.get_chat_history(chat_id=chat_id, offset_id=offset_id, limit=page_size):
                batch.append(msg)

            if not batch:
                break

            # قدیمی‌تر به جدیدتر (برای ثابت‌بودن ترتیب)
            batch = batch[::-1]
            ids = [m.id for m in batch]
            yield ids

            # offset_id را برای صفحه‌ی بعدی می‌بریم عقب‌تر
            offset_id = batch[0].id

    async def _forward_chunk(self, dst_id, src_id, mids: List[int]) -> int:
        """ارسال گروهی با fallback تکی و backoff نرم."""
        count = 0
        backoff = self._BACKOFF_BASE
        try:
            await self.client.forward_messages(dst_id, src_id, mids)
            return len(mids)
        except FloodWait as e:
            # برخی نسخه‌ها value یا x دارند
            wait = float(getattr(e, "value", getattr(e, "x", 0)) or backoff)
            jitter = wait * self._JITTER * (random.random() - 0.5) * 2
            sleep_for = max(1.0, min(self._BACKOFF_CAP, wait + jitter))
            logger.warning(f"⏳ FloodWait(chunk): sleeping {sleep_for:.1f}s")
            await asyncio.sleep(sleep_for)
            # retry once
            try:
                await self.client.forward_messages(dst_id, src_id, mids)
                return len(mids)
            except Exception:
                logger.warning("↪️ fallback to singles after FloodWait retry")
        except RPCError as e:
            logger.warning(f"⚠️ Chunk forward failed ({type(e).__name__}): fallback to singles")

        # fallback single
        for mid in mids:
            try:
                await self.client.forward_messages(dst_id, src_id, mid)
                count += 1
            except FloodWait as e:
                w = float(getattr(e, "value", getattr(e, "x", 0)) or backoff)
                j = w * self._JITTER * (random.random() - 0.5) * 2
                await asyncio.sleep(max(1.0, min(self._BACKOFF_CAP, w + j)))
            except Exception:
                # لاگ سطح پایین
                continue
            await asyncio.sleep(0.5)
        return count

    # -------------------------------
    # حلقه اصلی
    # -------------------------------
    async def _run(self) -> None:
        self.is_running = True
        try:
            while self.is_running:
                if not self.items or not self.targets:
                    # وقتی کاری نیست، بخواب تا busy-wait نشود
                    await asyncio.sleep(max(self._cycle_delay, 3.0))
                    continue

                # برای هر آیتم، از تاریخچه src صفحه‌به‌صفحه بخوان و به همهٔ تارگت‌ها بفرست
                for src, start_id, end_id in list(self.items):
                    src_id = await self._resolve(src)
                    if not src_id:
                        logger.warning(f"❌ منبع نامعتبر: {src}")
                        continue

                    async for page in self._iter_history_ids(src_id, self._PAGE_SIZE_DEFAULT):
                        # اگر رنج خاصی تعریف شده، فیلتر کنیم
                        mids = [m for m in page if (start_id is None or m >= start_id) and (end_id is None or m <= end_id)]
                        if not mids:
                            continue

                        # چانک‌چانک ارسال
                        for i in range(0, len(mids), self._CHUNK_SIZE_DEFAULT):
                            chunk = mids[i:i + self._CHUNK_SIZE_DEFAULT]
                            # به همهٔ تارگت‌ها
                            for dst in self.targets:
                                dst_id = await self._resolve(dst)
                                if not dst_id:
                                    logger.warning(f"❌ مقصد نامعتبر: {dst}")
                                    continue
                                sent = await self._forward_chunk(dst_id, src_id, chunk)
                                if sent:
                                    logger.info(f"✅ sent {sent} msgs: {src} → {dst}")
                                await asyncio.sleep(self.delay)

                        # وقفه بین صفحات
                        await asyncio.sleep(self._CYCLE_DELAY_DEFAULT)

                # وقفه بین دورها
                await asyncio.sleep(self._cycle_delay)
        finally:
            self.is_running = False
            logger.info("⛔ MultiForwarder loop stopped.")

    # -------------------------------
    # کنترل اجرا
    # -------------------------------
    def _on_task_done(self, task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.exception("💥 MultiForwarder loop crashed with exception", exc_info=e)

    def start(self) -> str:
        if self._task and not self._task.done():
            return "⚠️ قبلاً در حال اجراست."
        self._task = asyncio.create_task(self._run(), name="MultiForwarderLoop")
        self._task.add_done_callback(self._on_task_done)
        return "▶️ اجرا شد."

    def stop(self) -> str:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        return "🛑 عملیات متوقف شد."
