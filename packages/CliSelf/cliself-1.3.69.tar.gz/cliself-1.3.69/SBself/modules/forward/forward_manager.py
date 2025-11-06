# CliSelf/modules/forward_manager.py  (optimized for low CPU on shared hosts)
# ---------------------------------------------------------------------------
# تغییرات کلیدی جهت کاهش مصرف CPU بدون تغییر در کارکرد منطقی:
# - صفحه‌به‌صفحه پردازش (بدون جمع‌کردن کل آیدی‌ها در حافظه)
# - تاخیر قابل‌تنظیم و محافظه‌کارانه بین چانک‌ها و بین صفحات
# - backoff نمایی روی خطاها/FloodWait به‌همراه jitter
# - لاگ‌های سبک و خلاصه
# - اندازه چانک کوچک‌تر برای «تنفس» بیشتر CPU
#
# رفتار خروجی و قراردادها حفظ شده: همان پیام‌های موفقیت/خطا و همان ورودی‌ها.
# ---------------------------------------------------------------------------

import asyncio
import random
import urllib.parse as up
from typing import AsyncIterator, List, Optional

from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError

# توجه: مسیر logger در پروژه شما ممکن است متفاوت باشد؛ قرارداد قبلی حفظ شده است.
try:
    from ...core.logger import get_logger  # type: ignore
    logger = get_logger("forward")
except Exception:
    import logging
    logger = logging.getLogger("forward")
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO)


class ForwardManager:
    """
    ForwardManager
    ---------------
    مدیریت فوروارد پیام‌ها بین چت‌ها.
    شامل:
        - resolve_chat_id(): تشخیص و تبدیل ورودی (id, username, t.me link, 'me')
        - forward_all(): فوروارد تمام پیام‌ها از منبع به مقصد (بهینه‌شده برای CPU پایین)
    """

    # پارامترهای محافظه‌کارانه برای هاست اشتراکی/cPanel
    _PAGE_SIZE_DEFAULT: int = 100        # صفحه‌های کوچک‌تر برای کاهش فشار
    _CHUNK_SIZE_DEFAULT: int = 40        # بسته‌های کوچکتر → CPU و Flood بهتر
    _DELAY_BETWEEN_CHUNKS: float = 1.5   # تاخیر بین چانک‌ها
    _DELAY_BETWEEN_PAGES: float = 3.0    # تاخیر بین صفحه‌های تاریخچه
    _BACKOFF_BASE: float = 1.0           # شروع backoff نمایی
    _BACKOFF_CAP: float = 60.0           # سقف backoff
    _JITTER: float = 0.25                # درصد نویز برای جلوگیری از هم‌زمانی کامل

    def __init__(self, client: Client):
        self.client = client
        logger.info("ForwardManager initialized successfully (optimized).")

    # ----------------------------------------------------------
    # 🔹 تشخیص خودکار چت بر اساس ورودی (id, username, t.me link)
    # ----------------------------------------------------------
    async def resolve_chat_id(self, ident: str) -> Optional[int]:
        """
        تشخیص و برگرداندن chat_id از انواع ورودی‌ها:
        - عددی (chat_id)
        - username یا لینک t.me
        - 'me' برای پیام به خود شخص
        """
        if not ident:
            return None
        ident = ident.strip()
        if ident.lower() == "me":
            # pyrogram برای "me" معمولاً رشتهٔ 'me' را قبول می‌کند،
            # ولی جهت یکدستی با نوع int، همان 'me' را مستقیماً برمی‌گردانیم.
            # (خود pyrogram کار را انجام می‌دهد)
            return "me"  # type: ignore

        if "t.me/" in ident:
            ident = up.urlparse(ident).path.strip("/")

        # ورودی عددی؟
        if ident.lstrip("-").isdigit():
            num = int(ident)
            # اول چت، بعد کاربر
            try:
                c = await self.client.get_chat(num)
                return c.id  # type: ignore[return-value]
            except Exception:
                try:
                    u = await self.client.get_users(num)
                    return u.id  # type: ignore[return-value]
                except Exception:
                    return None

        # ورودی یوزرنیم یا لینک بدون عدد
        try:
            c = await self.client.get_chat(ident)
            return c.id  # type: ignore[return-value]
        except Exception:
            try:
                u = await self.client.get_users(ident)
                return u.id  # type: ignore[return-value]
            except Exception:
                return None

    # ----------------------------------------------------------
    # 🔹 ژنراتور تاریخچه: صفحه‌به‌صفحه و به ترتیب قدیمی→جدید
    # ----------------------------------------------------------
    async def _iter_history_ids(
        self,
        chat_id,
        page_size: int
    ) -> AsyncIterator[List[int]]:
        """
        تاریخچه را صفحه‌به‌صفحه می‌خواند و هر صفحه را (به ترتیب قدیمی→جدید) برمی‌گرداند.
        این رویکرد حافظه و CPU را سبک نگه می‌دارد.
        """
        offset_id = 0
        while True:
            batch = await self.client.get_chat_history(
                chat_id=chat_id,
                offset_id=offset_id,
                limit=page_size,
            )
            if not batch:
                break
            # get_chat_history جدید→قدیم است؛ برای ارسال قدیمی→جدید معکوس کنیم
            batch = list(batch)[::-1]
            ids = [m.id for m in batch]
            yield ids
            # برای صفحه بعد، قدیمی‌ترین پیام همین صفحه را offset کنیم
            offset_id = batch[0].id

    # ----------------------------------------------------------
    # 🔹 فوروارد تمام پیام‌ها از SRC به DEST (بهینه‌شده)
    # ----------------------------------------------------------
    async def forward_all(self, src: str, dst: str) -> str:
        """
        فوروارد تمام پیام‌ها از چت منبع (src) به چت مقصد (dst).
        پشتیبانی از ID، username، لینک t.me و 'me'.
        """
        src_id = await self.resolve_chat_id(src)
        dst_id = await self.resolve_chat_id(dst)

        if not src_id or not dst_id:
            logger.warning("SRC یا DEST نامعتبر است.")
            raise ValueError("SRC یا DEST نامعتبر است.")

        logger.info(f"🚀 Starting forward: {src} → {dst}")
        count = 0

        page_size = self._PAGE_SIZE_DEFAULT
        chunk_size = self._CHUNK_SIZE_DEFAULT
        delay_chunks = self._DELAY_BETWEEN_CHUNKS
        delay_pages = self._DELAY_BETWEEN_PAGES

        # backoff حالت سیال: بعد از موفقیت ریست می‌شود
        backoff = self._BACKOFF_BASE

        try:
            async for page_ids in self._iter_history_ids(src_id, page_size):
                if not page_ids:
                    await asyncio.sleep(delay_pages)
                    continue

                # صفحه را در چانک‌های کوچک ارسال کنیم
                for i in range(0, len(page_ids), chunk_size):
                    chunk = page_ids[i:i + chunk_size]
                    try:
                        await self.client.forward_messages(
                            chat_id=dst_id,
                            from_chat_id=src_id,
                            message_ids=chunk
                        )
                        count += len(chunk)
                        logger.info(f"✅ +{len(chunk)} (total {count})")

                        # موفقیت → backoff ریست شود
                        backoff = self._BACKOFF_BASE

                    except FloodWait as e:
                        # طبق مدت اعلام‌شده بخوابیم (با کمی jitter)
                        wait = float(getattr(e, "value", getattr(e, "x", 0)) or 0)
                        if wait <= 0:
                            wait = backoff
                        jitter = wait * self._JITTER * (random.random() - 0.5) * 2
                        sleep_for = max(1.0, min(self._BACKOFF_CAP, wait + jitter))
                        logger.warning(f"⏳ FloodWait: sleeping {sleep_for:.1f}s")
                        await asyncio.sleep(sleep_for)

                        # بعد از FloodWait تلاش مجدد برای همین chunk
                        try:
                            await self.client.forward_messages(
                                chat_id=dst_id,
                                from_chat_id=src_id,
                                message_ids=chunk
                            )
                            count += len(chunk)
                            logger.info(f"✅ (retry) +{len(chunk)} (total {count})")
                            backoff = self._BACKOFF_BASE
                        except Exception as ee:
                            # اگر دوباره شکست خورد، fallback به ارسال تکی
                            logger.warning(f"↪️ fallback to singles after FloodWait retry: {type(ee).__name__}")
                            count += await self._forward_chunk_safely_single(dst_id, src_id, chunk, backoff)

                            # backoff را کمی افزایش بدهیم برای دور بعد
                            backoff = min(self._BACKOFF_CAP, backoff * 2)

                    except RPCError as e:
                        # شکست گروهی → fallback به ارسال تکی
                        logger.warning(f"⚠️ Chunk forward failed ({type(e).__name__}): fallback to singles")
                        count += await self._forward_chunk_safely_single(dst_id, src_id, chunk, backoff)
                        backoff = min(self._BACKOFF_CAP, backoff * 2)

                    # تاخیر ثابت بین چانک‌ها (CPU تنفس کند)
                    await asyncio.sleep(delay_chunks)

                # بعد از اتمام هر صفحه، کمی استراحت
                await asyncio.sleep(delay_pages)

            logger.info(f"✅ Forward complete: {count} messages from {src} → {dst}")
            return f"✅ {count} پیام از {src} به {dst} فوروارد شد."

        except Exception as e:
            logger.error(f"💥 Error during forward_all: {type(e).__name__} - {e}")
            raise

    # ----------------------------------------------------------
    # 🔹 ارسال fallback: دانه‌دانه با تحمل خطا و backoff نرم
    # ----------------------------------------------------------
    async def _forward_chunk_safely_single(
        self,
        dst_id,
        src_id,
        chunk: List[int],
        backoff: float,
    ) -> int:
        sent = 0
        for mid in chunk:
            try:
                await self.client.forward_messages(dst_id, src_id, mid)
                sent += 1
                # موفقیت → backoff نرم را کم/ریست کنیم
                backoff = max(self._BACKOFF_BASE, backoff / 2)
            except FloodWait as e:
                wait = float(getattr(e, "value", getattr(e, "x", 0)) or backoff)
                jitter = wait * self._JITTER * (random.random() - 0.5) * 2
                sleep_for = max(1.0, min(self._BACKOFF_CAP, wait + jitter))
                logger.warning(f"⏳ FloodWait(single): sleeping {sleep_for:.1f}s")
                await asyncio.sleep(sleep_for)
            except Exception as ee:
                # پیام‌های محافظت‌شده/حذف‌شده/نامجاز را رد می‌کنیم
                logger.debug(f"↪️ skip msg {mid}: {type(ee).__name__} - {ee}")
                continue

            # مکث کوتاه بین ارسال‌های تکی برای جلوگیری از شلیک پیاپی
            await asyncio.sleep(0.5)

        return sent
