# -*- coding: utf-8 -*-
# File: CliSelf/SBself/modules/forward/forward_commands.py
#
# فرمان مستقل: saveall (یک‌بار اجرا؛ کل تاریخچه src → dest به ترتیب قدیم→جدید)
# ورودی‌ها: @username | عدد (user_id یا -100... برای گروه/کانال) | t.me/* | t.me/c/* | me
# حالت Reply: روی پیام از مبدا ریپلای بزن و بنویس: saveall to <DEST>

from __future__ import annotations

import re
import asyncio
from typing import List, Union, Optional

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram import errors as pyerrors

# فیلتر ادمین پروژه
try:
    from SBself.filters.SBfilters import admin_filter
except Exception:
    admin_filter = filters.all

# تنظیمات امن/بهینه
_SAFE_PAGE_SIZE_DEFAULT: int = 50
_SAFE_DELAY_BETWEEN_PAGES: float = 2.5
_SAFE_PER_MESSAGE_DELAY: float = 0.4

_saveall_lock = asyncio.Lock()

_RE_TME_C = re.compile(r"^(?:https?://)?t\.me/c/(\d+)(?:/\d+)?/?$", re.IGNORECASE)
_RE_TME_USERNAME = re.compile(r"^(?:https?://)?t\.me/(@?[A-Za-z0-9_]{5,})", re.IGNORECASE)


async def _normalize_ref(ref: str) -> str:
    s = (ref or "").strip()
    if not s:
        raise ValueError("ورودی خالی است.")
    if s.lower() == "me":
        return "me"
    if s.lstrip("-").isdigit():
        return s

    m = _RE_TME_C.match(s)  # t.me/c/<id>/...
    if m:
        internal = m.group(1)
        return f"-100{internal}"

    m = _RE_TME_USERNAME.match(s)  # t.me/username[/...]
    if m:
        uname = m.group(1)
        return uname[1:] if uname.startswith("@") else uname

    if s.startswith("@"):
        return s[1:]

    return s  # احتمالاً username


async def _resolve_ref(app: Client, ref: str) -> Union[str, int]:
    """
    - "me" → "me"
    - "-100..." → int کانال/سوپرگروه
    - عدد مثبت → تلاش برای کاربر با get_users(id)
      * اگر PeerIdInvalid: راهنمای تعامل اولیه.
    - username → با get_chat اعتبارسنجی
    """
    norm = await _normalize_ref(ref)

    if norm == "me":
        return "me"

    if norm.lstrip("-").isdigit():
        num = int(norm)
        if str(norm).startswith("-100"):
            await app.get_chat(num)
            return num
        try:
            user = await app.get_users(num)
            return int(user.id)
        except pyerrors.PeerIdInvalid:
            raise ValueError(
                "شناسهٔ عددی کاربر بدون «آشنایی» قابل resolve نیست (PEER_ID_INVALID).\n"
                "راه‌حل: از @username استفاده کن، یا یک‌بار با کاربر چت/تعامل داشته باش، "
                "یا روی پیامش ریپلای کن و بنویس:\n"
                "`saveall to me`"
            )
        except Exception as e:
            try:
                await app.get_chat(num)
                return num
            except Exception:
                raise ValueError(f"نشد resolve کنیم: {type(e).__name__}: {e}")

    await app.get_chat(norm)
    return norm


async def _source_from_reply(m: Message) -> Optional[Union[int, str]]:
    """اگر روی پیام ریپلای شده، مبدا را از همان پیام برگردان."""
    r = m.reply_to_message
    if not r:
        return None

    if r.chat and r.chat.id:
        return int(r.chat.id)

    # تلاش برای گرفتن منبع واقعی پیام فورواردی
    try:
        fo = getattr(r, "forward_origin", None)
        if fo and getattr(fo, "chat", None):
            sender_chat = getattr(fo.chat, "sender_chat", None) or fo.chat
            if getattr(sender_chat, "id", None):
                return int(sender_chat.id)
        if fo and getattr(fo, "sender_user", None):
            return int(fo.sender_user.id)
    except Exception:
        pass

    return None


async def _paged_history(app: Client, src: Union[str, int], page_size: int = _SAFE_PAGE_SIZE_DEFAULT):
    """
    صفحه‌به‌صفحه (async generator) با ترتیب نهایی قدیم→جدید.
    ✅ فیکس مهم: در اولین صفحه «max_id» را **نفرست**؛ برای صفحات بعدی از oldest_id-1 استفاده کن.
    """
    max_id: Optional[int] = None  # ← اینجا فیکس: اول None یعنی بدون سقف
    while True:
        batch: List[Message] = []

        # اگر max_id نداریم، پارامترش را اصلاً نفرستیم
        if max_id is None:
            async for msg in app.get_chat_history(chat_id=src, limit=page_size):
                batch.append(msg)
        else:
            async for msg in app.get_chat_history(chat_id=src, limit=page_size, max_id=max_id):
                batch.append(msg)

        if not batch:
            break

        batch.reverse()  # قدیم→جدید
        yield batch

        oldest_id = batch[0].id
        next_max = oldest_id - 1
        if next_max <= 0:
            break
        max_id = next_max  # از این به بعد max_id داریم


async def _forward_messages_ordered(
    app: Client,
    src: Union[str, int],
    dest: Union[str, int],
    delay_sec: float = _SAFE_PER_MESSAGE_DELAY,
    page_size: int = _SAFE_PAGE_SIZE_DEFAULT,
    delay_between_pages: float = _SAFE_DELAY_BETWEEN_PAGES,
) -> int:
    forwarded = 0
    seen: set[int] = set()

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
                # پیام protected/حذفی/… → رد
                continue

        if delay_between_pages > 0:
            await asyncio.sleep(delay_between_pages)

    return forwarded


def register(app: Client) -> None:
    @app.on_message(admin_filter & filters.command("saveall", prefixes=["/", ""]))
    async def _saveall_handler(client: Client, m: Message):
        """
        حالت‌ها:
          1) saveall <SRC> to <DEST>
          2) (Reply) روی پیامِ مبدا ریپلای بزن و بنویس:  saveall to <DEST>
        """
        text = (m.text or "").strip()
        parts = text.split()

        # حالت Reply: saveall to <DEST>
        if (
            m.reply_to_message
            and len(parts) >= 3
            and parts[0].lower() in ("saveall", "/saveall")
            and parts[1].lower() == "to"
        ):
            dest_ref = parts[2]
            src_ref = None
        else:
            # حالت کلاسیک
            if len(parts) < 4 or parts[0].lower() not in ("saveall", "/saveall") or parts[2].lower() != "to":
                return await m.reply(
                    "Usage:\n"
                    "  saveall <SRC> to <DEST>\n"
                    "یا در حالت ریپلای:\n"
                    "  (reply) saveall to <DEST>\n"
                    "مثال‌ها:\n"
                    "  saveall @ChannelA to me\n"
                    "  saveall 777000 to @backup\n"
                    "  (reply to message) saveall to me",
                    quote=True
                )
            src_ref = parts[1]
            dest_ref = parts[3]

        if _saveall_lock.locked():
            return await m.reply("⏳ یک عملیات `saveall` در حال اجراست. لطفاً صبر کنید.", quote=True)

        async with _saveall_lock:
            try:
                if src_ref is None:
                    src_from_reply = await _source_from_reply(m)
                    if src_from_reply is None:
                        return await m.reply(
                            "❌ نتونستم مبدا را از پیام ریپلای تشخیص بدم. "
                            "یا روی پیام درست ریپلای بزن، یا از الگوی «saveall <SRC> to <DEST>» استفاده کن.",
                            quote=True
                        )
                    src = src_from_reply
                else:
                    src = await _resolve_ref(client, src_ref)

                dest = await _resolve_ref(client, dest_ref)

            except Exception as e:
                return await m.reply(f"❌ منبع/مقصد نامعتبر است:\n{e}", quote=True)

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
            hint = ""
            if isinstance(src, int) and src > 0:
                hint = (
                    "\n\nنکته: اگر مبدا یک «کاربر با آی‌دی عددی مثبت» است و هنوز با او گفت‌وگو نداشتی، "
                    "ممکنه تاریخچه خالی دیده بشه. در این حالت از @username استفاده کن "
                    "یا روی یکی از پیام‌هاش ریپلای کن و بنویس `saveall to me`."
                )
            return await m.reply("هیچ پیامی فوروارد نشد (ممکن است چت خالی/محافظت‌شده باشد)." + hint, quote=True)

        return await m.reply(f"✅ {count} پیام با موفقیت فوروارد شد.", quote=True)
