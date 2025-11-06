# -*- coding: utf-8 -*-
# File: CliSelf/SBself/modules/forward/multi_forward_cmds.py
#
# دستورات سطح بالای «مولتی‌فوروارد» که توسط forward_commands.py صدا زده می‌شوند.
# این ماژول یک Singleton سبک از MultiForwarder را مدیریت می‌کند و فهرست پیام‌ها/تارگت‌ها
# را به‌صورت داخلی نگه می‌دارد؛ هنگام start_forward همه چیز را به Forwarder ست می‌کند.
#
# نکات بهینه‌سازی:
# - وقتی کاری نیست، حلقه‌ی اصلی Forwarder می‌خوابد → CPU پایین.
# - بین چانک‌ها/صفحات تاخیر محافظه‌کارانه داریم (قابل‌تنظیم با set_fdelay/set_fcycle).
# - روی Flood/خطاها backoff نمایی با jitter در خود MultiForwarder پیاده شده است.

from __future__ import annotations

from typing import Union, Optional, List, Tuple
from pyrogram.types import Message

# MultiForwarder بهینه‌شده (نسخه‌ای که قبل‌تر گذاشتیم)
from .multi_forward_manager import MultiForwarder

# -------------------------------
# وضعیت/تنظیمات ماژول (Singleton)
# -------------------------------
_forwarder: Optional[MultiForwarder] = None

# هر آیتم = (src_ref, start_id, end_id)
# برای ثبت «یک پیام خاص»، بازه را [mid, mid] می‌گذاریم
_ITEMS: List[Tuple[Union[int, str], Optional[int], Optional[int]]] = []

# فهرست مقصدها (chat_id عددی یا @username)
_TARGETS: List[Union[int, str]] = []

# تنظیمات پیش‌فرض ایمن برای هاست اشتراکی
_DELAY_BETWEEN_CHUNKS: float = 1.5   # set_fdelay
_CYCLE_DELAY: float = 3.0            # set_fcycle

# -------------------------------
# ابزارهای داخلی
# -------------------------------
def _ensure_forwarder(client) -> MultiForwarder:
    """اگر Singleton هنوز ساخته نشده، با Client بسازش."""
    global _forwarder
    if _forwarder is None:
        _forwarder = MultiForwarder(client)
        # ست اولیهٔ تنظیمات کم‌مصرف
        _forwarder.set_delay(_DELay_safe(_DELAY_BETWEEN_CHUNKS))
        _forwarder.set_cycle_delay(_Cycle_safe(_CYCLE_DELAY))
    return _forwarder

def _sync_config_to_forwarder() -> None:
    """لیست آیتم‌ها/تارگت‌ها و تاخیرها را به Forwarder اعمال کن."""
    if _forwarder is None:
        return
    _forwarder.set_items(_ITEMS)
    _forwarder.set_targets(_TARGETS)
    _forwarder.set_delay(_DELay_safe(_DELAY_BETWEEN_CHUNKS))
    _forwarder.set_cycle_delay(_Cycle_safe(_CYCLE_DELAY))

def _DELay_safe(x: float) -> float:
    # حداقل تاخیر معنادار برای جلوگیری از شلیک پیاپی
    try:
        xf = float(x)
    except Exception:
        xf = 1.0
    return max(0.5, min(xf, 60.0))

def _Cycle_safe(x: float) -> float:
    # حداقل وقفهٔ چرخه برای جلوگیری از busy-wait
    try:
        xf = float(x)
    except Exception:
        xf = 3.0
    return max(1.0, min(xf, 300.0))

def _dedupe_inplace(seq: List[Union[int, str]]) -> None:
    """حذف آیتم‌های تکراری درجا (حفظ ترتیب اولین مشاهده)."""
    seen = set()
    i = 0
    while i < len(seq):
        k = seq[i]
        if k in seen:
            del seq[i]
        else:
            seen.add(k)
            i += 1

def _append_item(src: Union[int, str], mid: int) -> None:
    """ثبت یک پیام منفرد به‌صورت بازه [mid, mid]."""
    # جلوگیری از آیتم‌های کاملاً تکراری
    item = (src, int(mid), int(mid))
    if item not in _ITEMS:
        _ITEMS.append(item)

# -------------------------------
# 📌 افزودن پیام (فقط فوروارد؛ کانال/گروه/پیوی)
# -------------------------------
async def add_fmsg(msg: Message, _unused: Optional[int] = None) -> str:
    """
    سناریوهای پشتیبانی‌شده:
      1) ریپلای روی پیام فورواردی از کانال/گروه:
         - اگر forward_from_chat و forward_from_message_id وجود داشت → همان منبع/آی‌دی فوروارد می‌شود.
      2) ریپلای روی خود پیام در گروه/سوپرگروه:
         - از chat.id همان گروه و message.id همان پیام استفاده می‌شود.
      3) ریپلای روی خود پیام در پیویِ شخص:
         - از chat.id همان پیوی و message.id همان پیام استفاده می‌شود (هدِر «Forwarded from <name>»).
      ⚠️ ریپلای در Saved Messages (me) پذیرفته نمی‌شود تا منبع «فرد» باقی بماند.
    """
    if not msg or not msg.reply_to_message:
        return "❗ برای ثبت پیام، روی خود پیام ریپلای کن (در پیوی شخص/گروه/یا پیام فورواردی)."

    src = msg.reply_to_message

    # 1) پیام فورواردی از کانال/گروه (دارای منبع واقعی)
    fchat = getattr(src, "forward_from_chat", None)
    fmsg_id = getattr(src, "forward_from_message_id", None)
    if fchat and fmsg_id:
        forward_chat_id: Union[int, str] = getattr(fchat, "id", None) or getattr(fchat, "username", None)
        if forward_chat_id is None:
            return "❌ شناسه‌ی منبع فوروارد در دسترس نیست."
        _append_item(forward_chat_id, int(fmsg_id))
        return f"✅ پیام فورواردی ثبت شد → from={forward_chat_id}, mid={fmsg_id}"

    # 2) جلوگیری از ثبت پیام داخل Saved Messages (me)
    chat_obj = src.chat
    if getattr(chat_obj, "is_self", False):  # Saved Messages
        return "❌ روی پیام داخل Saved Messages ریپلای نکن. لطفاً داخل **پیوی همان شخص** روی پیامش ریپلای کن تا منبع «از چه فردی» درست نمایش داده شود."

    # 3) پیام داخل گروه/سوپرگروه یا پیوی کاربر (غیرفوروارد)
    src_chat_id = chat_obj.id
    src_msg_id = src.id
    _append_item(src_chat_id, src_msg_id)
    return f"✅ پیام از چت جاری ثبت شد → chat={src_chat_id}, mid={src_msg_id}"

# -------------------------------
# پاکسازی/افزودن لیست‌ها
# -------------------------------
async def clear_fmsgs() -> str:
    _ITEMS.clear()
    return "🧹 لیست پیام‌ها پاک شد."

async def add_ftarget(chat_id: Union[int, str]) -> str:
    if isinstance(chat_id, str):
        chat_id = chat_id.strip()
        if not chat_id:
            return "❌ مقصد نامعتبر است."
    _TARGETS.append(chat_id)
    _dedupe_inplace(_TARGETS)
    return f"🎯 تارگت `{chat_id}` اضافه شد."

async def clear_ftargets() -> str:
    _TARGETS.clear()
    return "🧹 لیست تارگت‌ها پاک شد."

# -------------------------------
# تنظیم تاخیرها (کم‌مصرف)
# -------------------------------
async def set_fdelay(seconds: Union[int, float]) -> str:
    global _DELAY_BETWEEN_CHUNKS
    try:
        s = float(seconds)
    except Exception:
        return "❌ عدد معتبر وارد کن."
    _DELAY_BETWEEN_CHUNKS = _DELay_safe(s)
    if _forwarder:
        _forwarder.set_delay(_DELAY_BETWEEN_CHUNKS)
    return f"⏱ فاصله بین ارسال‌ها روی { _DELAY_BETWEEN_CHUNKS } ثانیه تنظیم شد."

async def set_fcycle(seconds: Union[int, float]) -> str:
    global _CYCLE_DELAY
    try:
        s = float(seconds)
    except Exception:
        return "❌ مقدار نامعتبر است."
    _CYCLE_DELAY = _Cycle_safe(s)
    if _forwarder:
        _forwarder.set_cycle_delay(_CYCLE_DELAY)
    return f"🔁 فاصله بین دورها روی { _CYCLE_DELAY } ثانیه تنظیم شد."

# -------------------------------
# کنترل اجرا
# -------------------------------
async def start_forward(client) -> str:
    """
    ساخت/هماهنگ‌سازی Forwarder و شروع حلقه.
    """
    fw = _ensure_forwarder(client)
    _sync_config_to_forwarder()
    # start در MultiForwarder هم‌زمانی ایجاد می‌کند و رشتهٔ وضعیت برمی‌گرداند
    return fw.start()

async def stop_forward() -> str:
    if _forwarder is None:
        return "ℹ️ چیزی در حال اجرا نیست."
    # stop در MultiForwarder تسک را cancel می‌کند و loop را تمیز می‌بندد
    return _forwarder.stop()

async def forward_status() -> str:
    # اگر Forwarder هنوز ساخته نشده باشد، وضعیت ماژول را گزارش کن
    if _forwarder is None:
        return (
            "📊 **وضعیت MultiForwarder**\n"
            f"🔹 آیتم‌ها: {len(_ITEMS)}\n"
            f"🔹 تارگت‌ها: {len(_TARGETS)}\n"
            f"⏱ فاصله ارسال (set_fdelay): { _DELAY_BETWEEN_CHUNKS } ثانیه\n"
            f"🔁 فاصله بین دورها (set_fcycle): { _CYCLE_DELAY } ثانیه\n"
            "🚦 فعال: ❌"
        )
    # در غیر این صورت، گزارش داخلی خود Forwarder را بده
    _sync_config_to_forwarder()
    return _forwarder.status()
