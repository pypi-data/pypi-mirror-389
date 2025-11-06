# -*- coding: utf-8 -*-
# File: CliSelf/SBself/moudels/forward/forward_commands.py
#
# رجیستر دستورات فوروارد:
#   - saveall <SRC> to <DEST>
#   - add_fmsg / clear_fmsgs
#   - add_ftarget / clear_ftargets
#   - set_fdelay / start_forward / stop_forward / forward_status
#   - (اختیاری) set_fcycle
#
# استفاده در main.py:
#   from SBself.moudels.forward.forward_commands import register as register_forward_commands
#   register_forward_commands(app)
#
# نکتهٔ بهینه‌سازی:
#   - برای کاهش مصرف CPU روی هاست‌هایی مثل cPanel، تاریخچه را صفحه‌به‌صفحه می‌خوانیم
#     (پیش‌فرض 100 پیام) و بین صفحات مکث کوتاهی داریم (پیش‌فرض 2 ثانیه). رفتار خروجی
#     تغییر نمی‌کند؛ فقط اجرای داخلی «نفس» پیدا می‌کند.
#   - اگر بخواهید مکث بین پیام‌ها داشته باشید، همان set_fdelay در مولتی‌فوروارد است؛
#     در saveall هم پارامتر delay_sec در کد پیش‌بینی شده ولی پیش‌فرض را 0 نگه داشته‌ایم
#     تا رفتار قدیمی حفظ شود.

import asyncio
from typing import Optional, List, Union, Tuple

from pyrogram import Client, filters
from pyrogram.types import Message

# فیلتر ادمین پروژه
try:
    from SBself.filters.SBfilters import admin_filter
except Exception:
    admin_filter = filters.all  # اگر ماژول فیلتر آماده نبود، همه مجاز (برای سازگاری)

# --- وارد کردن ابزارهای فوروارد تک‌مقصدی (طبق ساختار شما) -------------------
# این‌ها ابزارهای راه‌اندازی، مسیرها و تابع اصلی forward_all (در ماژول شما) را فراهم می‌کنند
try:
    from SBself.modules.forward.forward_cmds import init_forward_tools, forward_all
except Exception:
    # اگر ساختار کمی فرق داشت، مسیر دیگری را امتحان کنید یا این ایمپورت را با مسیر واقعی جایگزین کنید
    from SBself.modules.forward.forward_cmds import init_forward_tools, forward_all  # type: ignore

# --- وارد کردن دستورات مولتی‌فوروارد (صف و چند مقصد) -----------------------
try:
    from SBself.modules.forward.multi_forward_cmds import (
        add_fmsg, clear_fmsgs,
        add_ftarget, clear_ftargets,
        set_fdelay, set_fcycle,  # set_fcycle ممکن است اختیاری باشد
        start_forward, stop_forward, forward_status,
    )
except Exception:
    # اگر set_fcycle در پروژه‌تان نیست، اینجا می‌توانید آن را حذف کنید
    from SBself.modules.forward.multi_forward_cmds import (  # type: ignore
        add_fmsg, clear_fmsgs,
        add_ftarget, clear_ftargets,
        set_fdelay,
        start_forward, stop_forward, forward_status,
    )

# -----------------------------------------------------------------------------
# تنظیمات داخلی امن (برای saveall)
# -----------------------------------------------------------------------------
_SAFE_PAGE_SIZE_DEFAULT: int = 100         # صفحه‌های کوچکتر = فشار کمتر
_SAFE_DELAY_BETWEEN_PAGES: float = 2.0     # مکث کوتاه بین صفحات تاریخچه
_SAFE_PER_MESSAGE_DELAY: float = 0.0       # رفتار قدیمی: بدون مکث بین پیام‌ها (قابل تغییر در کد)


# --- کمک‌تابع‌ها -------------------------------------------------------------

async def _resolve_ref(app: Client, ref: str) -> Union[str, int]:
    """
    ورودی کاربر را به چیزی که Pyrogram می‌پذیرد تبدیل می‌کند:
    - "me" هم "me" می‌ماند
    - اگر به int تبدیل شود، عدد برمی‌گردد (برای آیدی‌های عددی مثل 777000 یا -100...)
    - در غیر این صورت همان رشته (یوزرنیم/لینک) برمی‌گردد
    و در نهایت با get_chat یک اعتبارسنجی سبک انجام می‌دهیم.
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

    # اعتبارسنجی سبک: اگر چت وجود نداشته باشد همین‌جا ارور می‌خوریم
    await app.get_chat(target)
    return target


async def _paged_history(app: Client, src: Union[str, int], page_size: int = _SAFE_PAGE_SIZE_DEFAULT):
    """
    صفحه‌بندی بدون offset_id (منسوخ). از max_id استفاده می‌کنیم.
    Pyrogram v2: get_chat_history یک async generator است.
    هر صفحه را new→old می‌دهد؛ ما reverse می‌کنیم تا old→new شود.
    """
    max_id = 0  # 0 = از جدیدترین شروع کن
    while True:
        batch: List[Message] = []
        async for msg in app.get_chat_history(chat_id=src, limit=page_size, max_id=max_id):
            batch.append(msg)

        if not batch:
            break

        # ترتیب ارسال قدیم→جدید
        batch.reverse()
        yield batch

        # برای صفحه‌ی بعدی: پیام‌های قدیمی‌تر از قدیمی‌ترینِ همین صفحه
        # چون قبل از reverse، batch به صورت new→old بود، قدیمی‌ترینِ واقعی = عنصر اول بعد از reverse
        oldest_id_in_this_page = batch[0].id
        max_id = oldest_id_in_this_page - 1
        if max_id <= 0:
            break

async def _forward_messages_ordered(
    app: Client,
    src: Union[str, int],
    dest: Union[str, int],
    delay_sec: float = _SAFE_PER_MESSAGE_DELAY,
    page_size: int = _SAFE_PAGE_SIZE_DEFAULT,
    delay_between_pages: float = _SAFE_DELAY_BETWEEN_PAGES,
) -> int:
    """
    همه‌ی پیام‌های src را به ترتیب زمانی به dest فوروارد می‌کند.
    - برای حفظ رفتار قدیمی، پیش‌فرض delay_sec=0.0 است (تغییری در خروجی نمی‌دهد)
    - برای کاهش مصرف، بین صفحات کمی می‌خوابیم (2s پیش‌فرض) تا CPU نفس بکشد.
    - پیام‌های protected/حذف‌شده نادیده گرفته می‌شوند.
    خروجی: تعداد پیام‌های موفق.
    """
    forwarded = 0
    async for page in _paged_history(app, src, page_size=page_size):
        for msg in page:
            try:
                await app.forward_messages(
                    chat_id=dest,
                    from_chat_id=src,
                    message_ids=msg.id
                )
                forwarded += 1
                if delay_sec > 0:
                    # اگر کاربر بخواهد، می‌تواند این را دستی تغییر دهد (برای saveall معمولاً 0 نگه می‌داریم)
                    await asyncio.sleep(delay_sec)
            except Exception:
                # پیام‌هایی که فورواردشان مجاز نیست/پاک شده‌اند/… را رد می‌کنیم
                continue

        # مکث کوتاه بین صفحات برای کاهش فشار CPU و ریسک Flood
        if delay_between_pages > 0:
            await asyncio.sleep(delay_between_pages)

    return forwarded


# --- فرمان اصلی: saveall ----------------------------------------------------
def register(app: Client) -> None:
    """
    این تابع را از main فراخوانی کنید تا دستورات فوروارد رجیستر شوند.
    هم ابزارهای فوروارد تک‌مقصدی را آماده می‌کند و هم دستورات مولتی‌فوروارد را.
    """
    # آماده‌سازی ابزارهای فوروارد تک‌مقصدی (در صورت نیاز)
    try:
        init_forward_tools(app)
    except Exception:
        # اگر برای اولین بار مسیرها/پوشه‌ها ساخته نشده بود، اجازه بده هندلرها بعداً آن را راه بیندازند
        pass

    # ---------------------- دستور SAVEALL (تک‌فوروارد) ----------------------
    @app.on_message(admin_filter & filters.command("saveall", prefixes=["/", ""]))
    async def _saveall_handler(client: Client, m: Message):
        """
        Usage:
            saveall <SRC> to <DEST>
        Examples:
            saveall @Rrabt to me
            saveall 777000 to me
            saveall @my_channel to @backup_channel
            saveall -1001234567890 to @somewhere
        """
        text = (m.text or "").strip()
        if not text:
            return await m.reply(
                "Usage:\n"
                "saveall <SRC> to <DEST>\n"
                "مثال: `saveall @Rrabt to me`",
                quote=True
            )

        parts = text.split()
        # انتظار شکل: saveall <SRC> to <DEST>
        if len(parts) < 4 or parts[0].lower() not in ("saveall", "/saveall") or parts[2].lower() != "to":
            return await m.reply(
                "Usage:\n"
                "saveall <SRC> to <DEST>\n"
                "مثال: `saveall @Rrabt to me`",
                quote=True
            )

        src_ref = parts[1]
        dest_ref = parts[3]

        # تبدیل مراجع و اعتبارسنجی
        try:
            src = await _resolve_ref(client, src_ref)
            dest = await _resolve_ref(client, dest_ref)
        except Exception as e:
            return await m.reply(f"❌ منبع/مقصد نامعتبر است: {e}", quote=True)

        # اجرای فوروارد با بهینه‌سازی داخلی (بین صفحات کمی می‌خوابیم)
        try:
            await m.reply("⏳ در حال فوروارد... لطفاً صبر کنید.", quote=True)
            count = await _forward_messages_ordered(
                client, src, dest,
                delay_sec=_SAFE_PER_MESSAGE_DELAY,
                page_size=_SAFE_PAGE_SIZE_DEFAULT,
                delay_between_pages=_SAFE_DELAY_BETWEEN_PAGES
            )
        except Exception as e:
            return await m.reply(f"⚠️ خطا در saveall: {e}", quote=True)

        if count == 0:
            return await m.reply("هیچ پیامی فوروارد نشد (ممکن است چت خالی/محافظت‌شده باشد).", quote=True)
        return await m.reply(f"✅ {count} پیام با موفقیت به مقصد فوروارد شد.", quote=True)

    # ---------------------- دستورات مولتی‌فوروارد (صف/چند مقصد) -------------
    @app.on_message(admin_filter & filters.command("add_fmsg", prefixes=["/", ""]))
    async def _add_fmsg(client: Client, m: Message):
        """
        اضافه‌کردن یک msg_id به صف پیام‌ها. اگر پارامتر ندهید و روی یک پیام ریپلای بزنید،
        همان پیام به‌عنوان msg_id استفاده می‌شود (در multi_forward_cmds باید پشتیبانی شده باشد).
        """
        msg_id: Optional[int] = None
        # اولویت: پارامتر عددی → ریپلای → خطا
        if m.text and len(m.command) > 1:
            try:
                msg_id = int(m.command[1])
            except Exception:
                return await m.reply("❌ msg_id نامعتبر است (باید عدد باشد).", quote=True)
        elif m.reply_to_message and m.reply_to_message.id:
            msg_id = int(m.reply_to_message.id)

        return await m.reply(await add_fmsg(m, msg_id))  # multi_forward_cmds

    @app.on_message(admin_filter & filters.command("clear_fmsgs", prefixes=["/", ""]))
    async def _clear_fmsgs(client: Client, m: Message):
        return await m.reply(await clear_fmsgs())

    @app.on_message(admin_filter & filters.command("add_ftarget", prefixes=["/", ""]))
    async def _add_ftarget(client: Client, m: Message):
        """
        افزودن مقصد (chat_id یا @username) به فهرست تارگت‌ها.
        """
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: `add_ftarget <chat_id|@username>`", quote=True)
        # اجازه بده هر دو حالت عددی و یوزرنیم پذیرفته شود
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
        """
        تنظیم تاخیر بین ارسال چانک‌ها در مولتی‌فوروارد.
        روی هاست‌های اشتراکی مقدار ≥ 1–2 ثانیه توصیه می‌شود.
        """
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: `set_fdelay <seconds>`", quote=True)
        try:
            seconds = float(m.command[1])
        except Exception:
            return await m.reply("❌ عدد معتبر وارد کن. مثال: `set_fdelay 1.5`", quote=True)
        if seconds < 0:
            seconds = 0.0
        return await m.reply(await set_fdelay(seconds))

    # set_fcycle ممکن است در برخی پروژه‌ها وجود نداشته باشد؛ اگر نبود، بلاک زیر را حذف کنید.
    @app.on_message(admin_filter & filters.command("set_fcycle", prefixes=["/", ""]))
    async def _set_fcycle(client: Client, m: Message):
        """
        تنظیم تاخیر بین دورهای کامل/صفحات در مولتی‌فوروارد.
        """
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: `set_fcycle <seconds>`", quote=True)
        try:
            seconds = float(m.command[1])
        except Exception:
            return await m.reply("❌ عدد معتبر وارد کن.", quote=True)
        if seconds < 0:
            seconds = 0.0
        return await m.reply(await set_fcycle(seconds))

    @app.on_message(admin_filter & filters.command("start_forward", prefixes=["/", ""]))
    async def _start_forward(client: Client, m: Message):
        """
        شروع مولتی‌فوروارد طبق صف پیام‌ها و فهرست تارگت‌ها.
        """
        return await m.reply(await start_forward(client))

    @app.on_message(admin_filter & filters.command("stop_forward", prefixes=["/", ""]))
    async def _stop_forward(client: Client, m: Message):
        """
        توقف مولتی‌فوروارد و آزادسازی منابع.
        """
        return await m.reply(await stop_forward())

    @app.on_message(admin_filter & filters.command("forward_status", prefixes=["/", ""]))
    async def _forward_status(client: Client, m: Message):
        """
        نمایش وضعیت فعلی مولتی‌فوروارد (تعداد پیام‌ها، تارگت‌ها، تاخیرها و فعال/غیرفعال بودن).
        """
        return await m.reply(await forward_status())


# ---------------
# راه‌اندازی ماژول
# ---------------
# اگر پروژهٔ شما الگوی auto-setup دارد، همین تابع را از main فراخوانی کنید:
#   register(app)
#
# در غیر این صورت، این ماژول را ایمپورت کنید و جایی که Client آماده است، یک‌بار:
#   register(app)
# صدا بزنید تا هندلرها رجیستر شوند.
