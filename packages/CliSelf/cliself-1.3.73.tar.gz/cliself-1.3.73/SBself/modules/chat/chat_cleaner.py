# chat_cleaner.py
# Compatible with Pyrogram v2
import asyncio
import logging
from typing import Iterable, List, Optional, Sequence, Union

from pyrogram import Client
from pyrogram.errors import FloodWait

logger = logging.getLogger(__name__)

# تلگرام در یک فراخوانی delete_messages تا 100 آی‌دی را می‌پذیرد
BATCH_SIZE = 100

def _chunks(seq: Sequence[int], size: int) -> Iterable[List[int]]:
    """Yield successive sized chunks from seq."""
    for i in range(0, len(seq), size):
        yield list(seq[i : i + size])

class ChatCleaner:
    """
    ابزار حذف پیام‌ها از چت‌ها.

    متدها:
      - clean_all(chat_id): تمام پیام‌های چت را حذف می‌کند.
      - del_last(chat_id, n): آخرین n پیام را حذف می‌کند.

    نکات:
      - نیاز به دسترسی کافی برای حذف پیام‌ها (به‌خصوص در گروه/کانال).
      - از get_chat_history (ژنراتور ناهمگام) استفاده می‌کند.
      - حذف‌ها در بچ‌های حداکثر 100تایی انجام می‌شود.
      - در FloodWait مکث منطقی دارد و سپس ادامه می‌دهد.
      - اگر حذف گروهی جایی خطا بدهد، تلاش می‌کند تک‌به‌تک پاک کند تا بیشترین تعداد ممکن حذف شود.
    """

    def __init__(self, client: Client, *, batch_size: int = BATCH_SIZE):
        if batch_size <= 0 or batch_size > 100:
            raise ValueError("batch_size must be between 1 and 100")
        self.client = client
        self.batch_size = batch_size
        logger.info("ChatCleaner initialized with batch_size=%d", self.batch_size)

    async def _delete_ids(self, chat_id: Union[int, str], ids: List[int]) -> int:
        """
        حذف مجموعه‌ای از آی‌دی‌ها با تحمل خطا:
        - ابتدا تلاشِ حذف گروهی
        - در صورت خطا، حذف تکی با ادامه‌ی کار
        """
        if not ids:
            return 0

        deleted = 0
        try:
            # حذف گروهی
            for chunk in _chunks(ids, self.batch_size):
                await self.client.delete_messages(chat_id, chunk, revoke=True)
                deleted += len(chunk)
        except FloodWait as e:
            # احترام به محدودیت تلگرام
            wait_s = int(getattr(e, "value", 5)) or 5
            logger.warning("FloodWait: sleeping %d seconds...", wait_s)
            await asyncio.sleep(wait_s)
            # تلاش دوباره برای باقی‌مانده‌ها
            remaining = ids[deleted:]
            for chunk in _chunks(remaining, self.batch_size):
                await self.client.delete_messages(chat_id, chunk, revoke=True)
                deleted += len(chunk)
        except Exception as e:
            # اگر حذف گروهی شکست خورد، به حذف تکی سقوط کن
            logger.warning("Bulk delete failed (%s). Falling back to single deletes.", type(e).__name__)
            for mid in ids:
                try:
                    await self.client.delete_messages(chat_id, mid, revoke=True)
                    deleted += 1
                except FloodWait as fw:
                    wait_s = int(getattr(fw, "value", 5)) or 5
                    logger.warning("FloodWait(single): sleeping %d seconds...", wait_s)
                    await asyncio.sleep(wait_s)
                    # بعد از خواب دوباره تلاش کن
                    try:
                        await self.client.delete_messages(chat_id, mid, revoke=True)
                        deleted += 1
                    except Exception:
                        pass
                except Exception:
                    # پیام‌هایی که اجازه‌ی حذف نداریم یا حذف‌شان ممکن نیست را رد کن
                    pass
                # کمی فاصله برای کاهش احتمال محدودیت
                await asyncio.sleep(0.03)

        return deleted

    async def clean_all(self, chat_id: Union[int, str]) -> int:
        """
        همه‌ی پیام‌های چت را حذف می‌کند.
        خروجی: تعداد پیام‌های حذف‌شده
        """
        total_deleted = 0
        batch: List[int] = []

        logger.info("Starting clean_all on chat_id=%s", chat_id)

        try:
            async for msg in self.client.get_chat_history(chat_id):
                batch.append(msg.id)
                if len(batch) >= self.batch_size:
                    total_deleted += await self._delete_ids(chat_id, batch)
                    batch.clear()
                    # مکث کوتاه برای کاهش احتمال FloodWait
                    await asyncio.sleep(0.15)

            # باقی‌مانده‌ها
            if batch:
                total_deleted += await self._delete_ids(chat_id, batch)
                batch.clear()

            logger.info("clean_all done. deleted=%d", total_deleted)
            return total_deleted

        except FloodWait as e:
            wait_s = int(getattr(e, "value", 5)) or 5
            logger.warning("FloodWait(history): sleeping %d seconds then resuming...", wait_s)
            await asyncio.sleep(wait_s)
            # پس از ادامه‌ی تاریخچه، تابع را بازصدا نمی‌کنیم؛
            # چون ژنراتور تاریخچه در میانه شکست خورده. برای سادگی:
            # کاربر می‌تواند دوباره فرمان را اجرا کند؛ یا اینجا می‌توان
            # حالت بازگشتی نوشت (ترجیح داده نشده که ساده و مطمئن بماند).
            return total_deleted
        except Exception as e:
            logger.error("clean_all failed: %s: %s", type(e).__name__, e)
            # هرچقدر تا اینجا حذف شده را برمی‌گردانیم
            return total_deleted

    async def del_last(self, chat_id: Union[int, str], n: int) -> int:
        """
        حذف آخرین n پیام (بدون توجه به فرستنده).
        خروجی: تعداد پیام‌های حذف‌شده
        """
        if n <= 0:
            return 0

        logger.info("Starting del_last n=%d on chat_id=%s", n, chat_id)

        # آی‌دی‌ها را به ترتیب نزولی از تاریخچه جمع می‌کنیم تا به n برسیم
        to_delete: List[int] = []
        try:
            async for msg in self.client.get_chat_history(chat_id):
                to_delete.append(msg.id)
                if len(to_delete) >= n:
                    break
        except FloodWait as e:
            wait_s = int(getattr(e, "value", 5)) or 5
            logger.warning("FloodWait(history): sleeping %d seconds then resuming...", wait_s)
            await asyncio.sleep(wait_s)
            # تلاش دوباره برای پرکردن to_delete
            async for msg in self.client.get_chat_history(chat_id):
                if msg.id in to_delete:
                    continue
                to_delete.append(msg.id)
                if len(to_delete) >= n:
                    break
        except Exception as e:
            logger.error("Reading history failed: %s: %s", type(e).__name__, e)

        if not to_delete:
            return 0

        # در صورتیکه کمتر از n پیام به دست آمد، همان مقدار موجود حذف می‌شود
        if len(to_delete) > n:
            to_delete = to_delete[:n]

        deleted = await self._delete_ids(chat_id, to_delete)
        logger.info("del_last done. requested=%d deleted=%d", n, deleted)
        return deleted
