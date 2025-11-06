# -*- coding: utf-8 -*-
# File: CliSelf/SBself/modules/forward/forward_commands.py
#
# دستورات فوروارد
# ───────────────
# این فایل دو بخش دارد:
# 1) saveall (کاملاً مستقل از سیستم مولتی‌فوروارد)  ← فقط یک بار اجرا می‌شود و تمام!
# 2) (اختیاری) دستورات مولتی‌فوروارد اگر بخواهید نگه دارید – اما saveall به آن‌ها وابسته نیست.
#
# استفاده:
#   saveall <SRC> to <DEST>
# مثال‌ها:
#   saveall @ChannelA to me
#   saveall -1001234567890 to @backup_chan
#   saveall 777000 to me

from __future__ import annotations

import asyncio
from typing import Optional, List, Union

from pyrogram import Client, filters
from pyrogram.types import Message

# فیلتر ادمین پروژه
try:
    from SBself.filters.SBfilters import admin_filter
except Exception:
    admin_filter = filters.all  # اگر ماژول فیلتر آماده نبود، موقتاً همه مجاز

# =============================================================================
# ⚡ تنظیمات امن/بهینه برای هاست‌های شلوغ
# =============================================================================
_SAFE_PAGE_SIZE_DEFAULT: int = 25          # تعداد پیام در هر صفحه (کوچکتر = فشار کمتر)
_SAFE_DELAY_BETWEEN_PAGES: float = 2.5     # مکث کوتاه بین صفحات
_SAFE_PER_MESSAGE_DELAY: float = 0.4       # مکث بین پیام‌ها (پیشنهاد: 0.2~0.4 اگر FloodWait دارید)

# جلوگیری از اجرای هم‌زمان چند saveall
_saveall_lock = asyncio.Lock()


# =============================================================================
# 🧩 ابزارهای داخلی مستقل از مولتی‌فوروارد
# =============================================================================
async def _resolve_ref(app: Client, ref: str) -> Union[str, int]:
    """
    ورودی کاربر را به چیزی که Pyrogram می‌پذیرد تبدیل می‌کند:
    - "me" هم همان "me" می‌ماند
    - اگر عدد باشد → int
    - در غیر این صورت رشته (یوزرنیم/لینک)
    و یک اعتبارسنجی سبک با get_chat انجام می‌دهد.
    """
    norm = (ref or "").strip()
    if not norm:
        raise ValueError("ورودی خالی است.")

    if norm.lower() == "me":
        target: Union[str, int] = "me"
    else:
        try:
            target = int(norm)
        except Exception:
            target = norm

    # اگر چت وجود نداشته باشد همین‌جا ارور می‌خورد
    await app.get_chat(target)
    return target


async def _paged_history(app: Client, src: Union[str, int], page_size: int = _SAFE_PAGE_SIZE_DEFAULT):
    """
    Pyrogram v2: get_chat_history یک async generator است که از جدید→قدیم می‌دهد.
    ما با پارامتر max_id صفحه‌بندی می‌کنیم و هر صفحه را reverse می‌کنیم تا قدیم→جدید شود.
    - بدون استفاده از offset_id (منسوخ).
    - max_id = oldest_id - 1  برای جلوگیری از تکرار.
    """
    max_id: int = 0  # 0 یعنی از جدیدترین‌ها شروع کن
    while True:
        batch: List[Message] = []
        async for msg in app.get_chat_history(chat_id=src, limit=page_size, max_id=max_id):
            batch.append(msg)

        if not batch:
            break

        batch.reverse()  # ترتیب old→new
        yield batch

        oldest_id = batch[0].id
        next_max = oldest_id - 1
        if next_max <= 0:
            break
        max_id = next_max


async def _forward_messages_ordered(
    app: Client,
    src: Union[str, int],
    dest: Union[str, int],
    delay_sec: float = _SAFE_PER_MESSAGE_DELAY,
    page_size: int = _SAFE_PAGE_SIZE_DEFAULT,
    delay_between_pages: float = _SAFE_DELAY_BETWEEN_PAGES,
) -> int:
    """
    همه‌ی پیام‌های src را به ترتیب زمانی (قدیم→جدید) به dest فوروارد می‌کند.
    - مستقل از هرگونه صف/لوپ دیگر
    - مقاوم در برابر پیام‌های محافظت‌شده/حذف‌شده
    - با مکث کوتاه بین صفحات برای کاهش فشار
    """
    forwarded = 0
    seen_ids: set[int] = set()  # پیشگیری از تکرار در صورت overlap نادر

    async for page in _paged_history(app, src, page_size=page_size):
        for msg in page:
            mid = msg.id
            if mid in seen_ids:
                continue
            seen_ids.add(mid)

            try:
                await app.forward_messages(
                    chat_id=dest,
                    from_chat_id=src,
                    message_ids=mid
                )
                forwarded += 1
                if delay_sec > 0:
                    await asyncio.sleep(delay_sec)
            except Exception:
                # پیام‌های محافظت‌شده/حذف‌شده/… را رد کن
                continue

        if delay_between_pages > 0:
            await asyncio.sleep(delay_between_pages)

    return forwarded


# =============================================================================
# 🧰 رجیستر دستورات
# =============================================================================
def register(app: Client) -> None:
    """
    این تابع را از main.py فراخوانی کنید:
        from SBself.modules.forward.forward_commands import register as register_forward_commands
        register_forward_commands(app)
    """

    # ---------------------- فرمان مستقل: SAVEALL ----------------------
    @app.on_message(admin_filter & filters.command("saveall", prefixes=["/", ""]))
    async def _saveall_handler(client: Client, m: Message):
        """
        Usage:
            saveall <SRC> to <DEST>

        Examples:
            saveall @ChannelA to me
            saveall 777000 to me
            saveall @my_channel to @backup_channel
            saveall -1001234567890 to @somewhere
        """
        text = (m.text or "").strip()
        if not text:
            return await m.reply(
                "Usage:\n"
                "saveall <SRC> to <DEST>\n"
                "مثال: `saveall @ChannelA to me`",
                quote=True
            )

        parts = text.split()
        # شکل معتبر: saveall <SRC> to <DEST>
        if len(parts) < 4 or parts[0].lower() not in ("saveall", "/saveall") or parts[2].lower() != "to":
            return await m.reply(
                "Usage:\n"
                "saveall <SRC> to <DEST>\n"
                "مثال: `saveall @ChannelA to me`",
                quote=True
            )

        src_ref = parts[1]
        dest_ref = parts[3]

        # جلوگیری از اجرای هم‌زمان
        if _saveall_lock.locked():
            return await m.reply("⏳ یک عملیات `saveall` در حال اجراست. لطفاً صبر کنید.", quote=True)

        async with _saveall_lock:
            # تبدیل و اعتبارسنجی مراجع
            try:
                src = await _resolve_ref(client, src_ref)
                dest = await _resolve_ref(client, dest_ref)
            except Exception as e:
                return await m.reply(f"❌ منبع/مقصد نامعتبر است: {e}", quote=True)

            # اجرای فوروارد یک‌باره و مستقل
            try:
                await m.reply("⏳ در حال فوروارد... لطفاً صبر کنید.", quote=True)
                count = await _forward_messages_ordered(
                    client,
                    src,
                    dest,
                    delay_sec=_SAFE_PER_MESSAGE_DELAY,
                    page_size=_SAFE_PAGE_SIZE_DEFAULT,
                    delay_between_pages=_SAFE_DELAY_BETWEEN_PAGES
                )
            except Exception as e:
                return await m.reply(f"⚠️ خطا در saveall: {e}", quote=True)

        if count == 0:
            return await m.reply("هیچ پیامی فوروارد نشد (ممکن است چت خالی/محافظت‌شده باشد).", quote=True)
        return await m.reply(f"✅ {count} پیام با موفقیت فوروارد شد.", quote=True)


    # ========================================================================
    # (اختیاری) اگر همچنان می‌خواهید دستورات مولتی‌فوروارد را نگه دارید،
    #          در یک بخش کاملاً جداگانه رجیسترشان کنید. ولی «saveall»
    #          هیچ وابستگی‌ای به این بخش ندارد.
    # ========================================================================
    try:
        from SBself.modules.forward.multi_forward_cmds import (
            add_fmsg, clear_fmsgs,
            add_ftarget, clear_ftargets,
            set_fdelay,
            # اگر set_fcycle دارید، بازش کنید:
            # set_fcycle,
            start_forward, stop_forward, forward_status,
        )

        @app.on_message(admin_filter & filters.command("add_fmsg", prefixes=["/", ""]))
        async def _add_fmsg(client: Client, m: Message):
            msg_id: Optional[int] = None
            if m.text and len(m.command) > 1:
                try:
                    msg_id = int(m.command[1])
                except Exception:
                    return await m.reply("❌ msg_id نامعتبر است (عدد بده).", quote=True)
            elif m.reply_to_message and m.reply_to_message.id:
                msg_id = int(m.reply_to_message.id)
            return await m.reply(await add_fmsg(m, msg_id))

        @app.on_message(admin_filter & filters.command("clear_fmsgs", prefixes=["/", ""]))
        async def _clear_fmsgs(client: Client, m: Message):
            return await m.reply(await clear_fmsgs())

        @app.on_message(admin_filter & filters.command("add_ftarget", prefixes=["/", ""]))
        async def _add_ftarget(client: Client, m: Message):
            if not (m.text and len(m.command) > 1):
                return await m.reply("Usage: `add_ftarget <chat_id|@username>`", quote=True)
            try:
                chat_id: Union[int, str] = int(m.command[1])
            except Exception:
                chat_id = m.command[1].strip()
            return await m.reply(await add_ftarget(chat_id))

        @app.on_message(admin_filter & filters.command("clear_ftargets", prefixes=["/", ""]))
        async def _clear_ftargets(client: Client, m: Message):
            return await m.reply(await clear_ftargets())

        @app.on_message(admin_filter & filters.command("set_fdelay", prefixes=["/", ""]))
        async def _set_fdelay(client: Client, m: Message):
            if not (m.text and len(m.command) > 1):
                return await m.reply("Usage: `set_fdelay <seconds>`", quote=True)
            try:
                seconds = float(m.command[1])
            except Exception:
                return await m.reply("❌ عدد معتبر وارد کن. مثال: `set_fdelay 1.5`", quote=True)
            if seconds < 0:
                seconds = 0.0
            return await m.reply(await set_fdelay(seconds))

        # اگر set_fcycle دارید، این بلاک را باز کنید:
        # @app.on_message(admin_filter & filters.command("set_fcycle", prefixes=["/", ""]))
        # async def _set_fcycle(client: Client, m: Message):
        #     if not (m.text and len(m.command) > 1):
        #         return await m.reply("Usage: `set_fcycle <seconds>`", quote=True)
        #     try:
        #         seconds = float(m.command[1])
        #     except Exception:
        #         return await m.reply("❌ عدد معتبر وارد کن.", quote=True)
        #     if seconds < 0:
        #         seconds = 0.0
        #     return await m.reply(await set_fcycle(seconds))

        @app.on_message(admin_filter & filters.command("start_forward", prefixes=["/", ""]))
        async def _start_forward(client: Client, m: Message):
            return await m.reply(await start_forward(client))

        @app.on_message(admin_filter & filters.command("stop_forward", prefixes=["/", ""]))
        async def _stop_forward(client: Client, m: Message):
            return await m.reply(await stop_forward())

        @app.on_message(admin_filter & filters.command("forward_status", prefixes=["/", ""]))
        async def _forward_status(client: Client, m: Message):
            return await m.reply(await forward_status())

    except Exception:
        # اگر ماژول مولتی‌فوروارد نصب/موجود نبود، بی‌سروصدا نادیده بگیر
        pass
