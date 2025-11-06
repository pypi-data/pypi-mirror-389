# -*- coding: utf-8 -*-
# File: CliSelf/SBself/modules/profile_manager.py

from pyrogram import Client
from pyrogram.types import Message
from ...config import AllConfig
from typing import Optional, Union
from pyrogram.errors import UsernameOccupied, UsernameInvalid, FloodWait
import re
import asyncio
try:
    from ...core.logger import get_logger
    logger = get_logger("profile_manager")
except Exception:
    import logging
    logger = logging.getLogger("profile_manager")


# -------------------------------
# 🧍‍♂️ تغییر نام پروفایل
# -------------------------------
async def update_name(app: Client, new_name: str) -> str:
    if not new_name.strip():
        return "❌ نام وارد نشده."
    try:
        await app.update_profile(first_name=new_name.strip())
        logger.info(f"✅ Name updated to: {new_name.strip()}")
        return f"✅ نام به '{new_name.strip()}' تغییر یافت."
    except Exception as e:
        logger.error(f"⚠️ Error updating name: {e}")
        return f"⚠️ خطا در تغییر نام: {e}"


# -------------------------------
# 🧾 تغییر بیوگرافی
# -------------------------------
async def update_bio(app: Client, new_bio: str) -> str:
    if not new_bio.strip():
        return "❌ بیو خالی است."
    try:
        await app.update_profile(bio=new_bio.strip())
        logger.info("✅ Bio updated.")
        return "✅ بیو تغییر یافت."
    except Exception as e:
        logger.error(f"⚠️ Error updating bio: {e}")
        return f"⚠️ خطا در تغییر بیو: {e}"


# -------------------------------
# 💬 تغییر نام کاربری (username)
# -------------------------------
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{5,32}$")

async def update_username(app: Client, new_username: str) -> str:
    new_username = (new_username or "").strip().lstrip("@")
    if not new_username:
        return "❌ یوزرنیم خالی است."

    if not USERNAME_RE.fullmatch(new_username):
        return "⚠️ یوزرنیم نامعتبر است. فقط حروف لاتین، عدد و _ با طول ۵ تا ۳۲."

    try:
        ok = await app.set_username(new_username)  # متد درست در Pyrogram v2
        if ok:
            logger.info("✅ Username updated to @%s", new_username)
            return f"✅ یوزرنیم به @{new_username} تغییر یافت."
        return "⚠️ تغییری اعمال نشد."
    except UsernameOccupied:
        return "⚠️ این یوزرنیم قبلاً گرفته شده."
    except UsernameInvalid:
        return "⚠️ یوزرنیم نامعتبر است."
    except FloodWait as e:
        # تلگرام محدودیت اعمال کرده
        return f"⏳ محدودیت تلگرام فعال است. بعد از {e.value} ثانیه دوباره تلاش کنید."
    except Exception as e:
        logger.exception("⚠️ Error updating username")
        return f"⚠️ خطا در تغییر یوزرنیم: {e}"

# -------------------------------
# 🖼️ تغییر عکس پروفایل
# -------------------------------
async def update_photo(app: Client, message: Message) -> str:
    """
    تغییر عکس پروفایل با ریپلای روی تصویر جدید.
    """
    if not message.reply_to_message or not message.reply_to_message.photo:
        return "❌ روی تصویری ریپلای بزن تا عکس پروفایل تغییر کند."
    try:
        path = await message.reply_to_message.download()
        await app.set_profile_photo(photo=path)
        logger.info(f"🖼️ Profile photo updated: {path}")
        return "✅ عکس پروفایل تغییر یافت."
    except Exception as e:
        logger.error(f"⚠️ Error updating photo: {e}")
        return f"⚠️ خطا در تغییر عکس پروفایل: {e}"


# -------------------------------
# 🧹 حذف عکس فعلی
# -------------------------------
def _normalize_limit(limit: Optional[Union[int, str]]) -> Optional[int]:
    """
    برگرداندن limit نرمال‌شده:
      - None / 'all' / '*' / عدد <= 0  ➜ None (همه عکس‌ها)
      - عدد مثبت ➜ همان عدد
      - رشتهٔ عددی ➜ تبدیل به int
    """
    if limit is None:
        return None
    if isinstance(limit, str):
        s = limit.strip().lower()
        if s in {"all", "*", "∞"}:
            return None
        try:
            limit = int(s)
        except ValueError:
            # مقدار نامعتبر → همه
            return None
    # حالا limit قطعاً int است
    return None if limit <= 0 else int(limit)

async def clear_photo(app: Client, limit: Optional[Union[int, str]] = 1) -> str:
    """
    حذف عکس(های) پروفایل کاربر.
    - limit=1  ➜ حذف یک عکس (جدیدترین)
    - limit=n  ➜ حذف n عکس
    - limit=None / 'all' / '*' / n<=0  ➜ حذف همهٔ عکس‌ها
    """
    try:
        norm_limit = _normalize_limit(limit)

        # photos را به لیست تبدیل می‌کنیم
        if norm_limit is None:
            photos = [p async for p in app.get_chat_photos("me")]
        else:
            photos = [p async for p in app.get_chat_photos("me", limit=norm_limit)]

        if not photos:
            return "⚠️ هیچ عکس فعالی وجود ندارد."

        # حذف بر اساس file_id
        await app.delete_profile_photos([p.file_id for p in photos])

        logger.info("🧹 Profile photo cleared: %d deleted.", len(photos))
        if norm_limit is None:
            return f"🧹 همهٔ عکس‌های پروفایل حذف شد. (تعداد: {len(photos)})"
        return f"🧹 {len(photos)} عکس پروفایل حذف شد."
    except FloodWait as e:
        return f"⏳ محدودیت تلگرام فعال است. بعد از {e.value} ثانیه دوباره تلاش کنید."
    except Exception as e:
        logger.exception("⚠️ Error clearing photo")
        return f"⚠️ خطا در حذف عکس پروفایل: {e}"    

# -------------------------------
# 📊 نمایش وضعیت فعلی پروفایل
# -------------------------------
async def show_profile_status(app: Client) -> str:
    try:
        me = await app.get_me()
        text = (
            "📋 **وضعیت فعلی پروفایل:**\n"
            f"👤 نام: {me.first_name or '—'} {me.last_name or ''}\n"
            f"💬 بیو: {me.bio or '—'}\n"
            f"🔗 یوزرنیم: @{me.username if me.username else '—'}\n"
            f"🆔 شناسه: `{me.id}`"
        )
        return text
    except Exception as e:
        logger.error(f"⚠️ Error getting profile status: {e}")
        return f"⚠️ خطا در گرفتن اطلاعات پروفایل: {e}"
