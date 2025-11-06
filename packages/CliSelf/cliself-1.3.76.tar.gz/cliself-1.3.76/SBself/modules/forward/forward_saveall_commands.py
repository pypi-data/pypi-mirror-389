# -*- coding: utf-8 -*-
# File: CliSelf/SBself/modules/forward/forward_commands.py
#
# فرمان مستقل: saveall
# ─────────────────────
# یک‌بار اجرا می‌شود؛ کل تاریخچه‌ی مبدا را به مقصد فوروارد می‌کند (قدیم→جدید).
# ورودی‌های معتبر برای <SRC> و <DEST>:
#   - @username
#   - آیدی عددی (777000، -1001234567890)
#   - لینک t.me/username یا t.me/username/123
#   - لینک t.me/c/<internal_id>/<msg>  → خودش به -100<internal_id> تبدیل می‌شود
#   - me  (Saved Messages)
#
# استفاده:
#   saveall <SRC> to <DEST>
# مثال‌ها:
#   saveall @ChannelA to me
#   saveall 777000 to @backup_chan
#   saveall https://t.me/c/123456/789 to -1001122334455
#   saveall t.me/username to @somewhere

from __future__ import annotations

import re
import asyncio
from typing import Optional, List, Union

from pyrogram import Client, filters
from pyrogram.types import Message

# فیلتر ادمین پروژه
try:
    from SBself.filters.SBfilters import admin_filter
except Exception:
    admin_filter = filters.all  # اگر ماژول فیلتر حاضر نبود، موقتا همه مجاز

# تنظیمات امن/بهینه
_SAFE_PAGE_SIZE_DEFAULT: int = 50          # تعداد پیام در هر صفحه
_SAFE_DELAY_BETWEEN_PAGES: float = 2.5     # مکث بین صفحات
_SAFE_PER_MESSAGE_DELAY: float = 0.4       # مکث بین هر پیام (در صورت FloodWait، این را 0.2~0.4 بگذارید)

# جلوگیری از اجراهای هم‌زمان
_saveall_lock = asyncio.Lock()

# الگوهای تشخیص ورودی
_RE_TME_C = re.compile(r"^(?:https?://)?t\.me/c/(\d+)(?:/\d+)?/?$", re.IGNORECASE)
_RE_TME_USERNAME = re.compile(r"^(?:https?://)?t\.me/(@?[A-Za-z0-9_]{5,})", re.IGNORECASE)


async def _normalize_ref(ref: str) -> str:
    """
    ورودی کاربر را نرمال می‌کند تا قابل‌حل باشد:
      - me → me
      - @username → username
      - t.me/username → username
      - t.me/username/123 → username
      - t.me/c/<id>/... → -100<id>
      - آیدی عددی را همان رشته تحویل می‌دهد
    """
    s = (ref or "").strip()
    if not s:
        raise ValueError("ورودی خالی است.")
    if s.lower() == "me":
        return "me"

    # آیدی عددی؟
    if s.lstrip("-").isdigit():
        return s

    # لینک t.me/c/123456[/...]
    m = _RE_TME_C.match(s)
    if m:
        internal = m.group(1)  # مثل 123456
        return f"-100{internal}"

    # لینک t.me/username[/...]
    m = _RE_TME_USERNAME.match(s)
    if m:
        uname = m.group(1)
        if uname.startswith("@"):
            uname = uname[1:]
        return uname

    # @username → username
    if s.startswith("@"):
        return s[1:]

    # در غیر اینصورت همان رشته (یوزرنیم)
    return s


async def _resolve_ref(app: Client, ref: str) -> Union[str, int]:
    """
    رشته‌ی نرمال‌شده را به چیزی که Pyrogram می‌پذیرد تبدیل می‌کند و اعتبارسنجی می‌کند.
    - "me" همان "me" می‌ماند.
    - اگر عدد باشد → int
    - در غیر این صورت → یوزرنیم/لینک؛ با get_chat اعتبارسنجی می‌کنیم.
    """
    norm = await _normalize_ref(ref)

    if norm == "me":
        target: Union[str, int] = "me"
    elif norm.lstrip("-").isdigit():
        target = int(norm)
    else:
        target = norm  # username

    # اعتبارسنجی سبک (وجود/دسترسی چت)
    await app.get_chat(target)
    return target


async def _paged_history(app: Client, src: Union[str, int], page_size: int = _SAFE_PAGE_SIZE_DEFAULT):
    """
    صفحه‌به‌صفحه تاریخچه را می‌دهد (Pyrogram v2: async generator، جدید→قدیم).
    با max_id صفحه‌بندی می‌کنیم و هر صفحه را reverse می‌کنیم تا قدیم→جدید شود.
    """
    max_id: int = 0  # 0 = از جدیدترین شروع کن
    while True:
        batch: List[Message] = []
        # async generator → جمع‌آوری صفحه
        async for msg in app.get_chat_history(chat_id=src, limit=page_size, max_id=max_id):
            batch.append(msg)

        if not batch:
            break

        batch.reverse()  # ترتیبی: قدیم→جدید
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
    همه پیام‌های src را به ترتیب زمانی (قدیم→جدید) به dest فوروارد می‌کند.
    پیام‌های محافظت‌شده/حذف‌شده نادیده گرفته می‌شوند.
    """
    forwarded = 0
    seen: set[int] = set()  # احتیاط برای جلوگیری از تکرار

    async for page in _paged_history(app, src, page_size=page_size):
        for msg in page:
            mid = msg.id
            if mid in seen:
                continue
            seen.add(mid)

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
                # protected/deleted/… → رد
                continue

        if delay_between_pages > 0:
            await asyncio.sleep(delay_between_pages)

    return forwarded


def register(app: Client) -> None:
    """
    رجیستر دستور saveall.
    از main.py:
        from SBself.modules.forward.forward_commands import register as register_forward_commands
        register_forward_commands(app)
    """

    @app.on_message(admin_filter & filters.command("saveall", prefixes=["/", ""]))
    async def _saveall_handler(client: Client, m: Message):
        """
        Usage:
            saveall <SRC> to <DEST>

        Examples:
            saveall @ChannelA to me
            saveall 777000 to @backup_chan
            saveall https://t.me/username to -1001234567890
            saveall t.me/c/123456/789 to me
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

        # جلوگیری از هم‌زمانی چند saveall
        if _saveall_lock.locked():
            return await m.reply("⏳ یک عملیات `saveall` در حال اجراست. لطفاً صبر کنید.", quote=True)

        async with _saveall_lock:
            # تبدیل و اعتبارسنجی مراجع
            try:
                src = await _resolve_ref(client, src_ref)
                dest = await _resolve_ref(client, dest_ref)
            except Exception as e:
                return await m.reply(f"❌ منبع/مقصد نامعتبر است: {e}", quote=True)

            # اجرای مستقل و یک‌باره
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
