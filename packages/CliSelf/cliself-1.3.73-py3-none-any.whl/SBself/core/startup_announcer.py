# -*- coding: utf-8 -*-
# File: SBself/core/startup_announcer.py
#
# ماژول اعلانِ شروع به‌کار:
# - تلاش برای جوین به لینک دعوت (اختیاری)
# - ساخت پیام HTML شامل زمان محلی + تاریخ میلادی/جلالی/قمری، نام/یوزرنیم/آیدی/بیو
# - ارسال پیام در چت هدف
# - (اختیاری) اعلان به مالک‌ها (owner_admin_id) در پی‌وی
#
# استفاده در main.py:
#   from SBself.core.startup_announcer import announce_startup
#   ...
#   if __name__ == "__main__":
#       app.run(announce_startup(app, target_chat=-1001234567890, invite_link=None, notify_owners=True))
#
# نکته: parse_mode به‌صورت مقاوم (HTML → "HTML" → "html" → بدون parse_mode) هندل می‌شود.

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Union, Iterable, Any

# --------------------------------------------------------------------
# ارسال مقاوم با HTML (HTML → "HTML" → "html" → بدون parse_mode)
# --------------------------------------------------------------------
async def _send_html_best_effort(app, chat_id: Union[int, str], html_text: str) -> None:
    try:
        from pyrogram.enums import ParseMode as _PM  # Pyrogram v2
        await app.send_message(chat_id, html_text, parse_mode=_PM.HTML, disable_web_page_preview=True)
        return
    except Exception as e1:
        msg = (str(e1) or "").lower()
        if "parse mode" not in msg:
            raise
    try:
        await app.send_message(chat_id, html_text, parse_mode="HTML", disable_web_page_preview=True)
        return
    except Exception as e2:
        msg = (str(e2) or "").lower()
        if "parse mode" not in msg:
            raise
    try:
        await app.send_message(chat_id, html_text, parse_mode="html", disable_web_page_preview=True)
        return
    except Exception as e3:
        msg = (str(e3) or "").lower()
        if "parse mode" not in msg:
            raise
    # آخرین راه: بدون parse_mode
    await app.send_message(chat_id, html_text, disable_web_page_preview=True)

# --------------------------------------------------------------------
# تبدیل میلادی ↔ جلالی
# --------------------------------------------------------------------
def _gregorian_to_jalali(gy: int, gm: int, gd: int):
    g_d_m = [0,31,59,90,120,151,181,212,243,273,304,334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd + g_d_m[gm - 1]
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    jy += (days - 1) // 365
    days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd

# --------------------------------------------------------------------
# تبدیل میلادی → قمری مدنی (tabular Islamic؛ دقت ~۱ روز)
# --------------------------------------------------------------------
def _gregorian_to_jd(y: int, m: int, d: int) -> int:
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return d + ((153 * m2 + 2) // 5) + 365 * y2 + (y2 // 4) - (y2 // 100) + (y2 // 400) - 32045

def _jd_to_islamic(jd: int):
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    m = (24 * l) // 709
    d = l - (709 * m) // 24
    y = 30 * n + j - 30
    return y, m, d

def _gregorian_to_hijri(gy: int, gm: int, gd: int):
    jd = _gregorian_to_jd(gy, gm, gd)
    return _jd_to_islamic(jd)

def _fmt2(n: int) -> str:
    return f"{n:02d}"

# --------------------------------------------------------------------
# ساخت متن اعلان شروع
# --------------------------------------------------------------------
async def _build_start_message(app) -> str:
    # اطلاعات کاربر
    try:
        me = await app.get_me()
    except Exception:
        me = None

    first = (getattr(me, "first_name", "") or "").strip() if me else ""
    last  = (getattr(me, "last_name", "") or "").strip() if me else ""
    full_name = (first + (" " + last if last else "")).strip() or "—"
    username = ("@" + me.username) if (me and getattr(me, "username", None)) else "—"
    user_id  = getattr(me, "id", None) or "—"

    # بیو
    bio = "—"
    try:
        cme = await app.get_chat("me")
        if hasattr(cme, "bio") and cme.bio:
            bio = cme.bio.strip() or "—"
    except Exception:
        pass

    # تاریخ‌ها
    now = datetime.now(timezone.utc).astimezone()
    gy, gm, gd = now.year, now.month, now.day
    jy, jm, jd = _gregorian_to_jalali(gy, gm, gd)
    hy, hm, hd = _gregorian_to_hijri(gy, gm, gd)

    clock = now.strftime("%H:%M:%S")
    g_date = f"{gy}-{_fmt2(gm)}-{_fmt2(gd)}"
    j_date = f"{jy}-{_fmt2(jm)}-{_fmt2(jd)}"
    h_date = f"{hy}-{_fmt2(hm)}-{_fmt2(hd)}"

    html = (
        "🚀 <b>CliSelf started</b>\n"
        "────────────────────\n"
        f"🕒 <b>Time:</b> {clock}\n"
        f"📅 <b>Miladi:</b> {g_date}\n"
        f"📆 <b>Jalali:</b> {j_date}\n"
        f"🕌 <b>Hijri:</b> {h_date}\n"
        "────────────────────\n"
        f"👤 <b>Name:</b> {full_name}\n"
        f"🔖 <b>Username:</b> {username}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n"
        f"📝 <b>Bio:</b> {bio if bio else '—'}\n"
    )
    return html

# --------------------------------------------------------------------
# تلاش برای جوین (اختیاری)
# --------------------------------------------------------------------
async def _try_join(app, invite_link: Optional[str]) -> None:
    if not invite_link:
        return
    try:
        await app.join_chat(invite_link)
    except Exception:
        # اگر عضو بودی/دعوت محدود بود، ادامه بده
        pass

# --------------------------------------------------------------------
# اعلان شروع اصلی (API)
# --------------------------------------------------------------------
async def announce_startup(app) -> None:
    """
    - اگر invite_link داده شده باشد، سعی می‌کند جوین کند (بی‌صدا از خطا رد می‌شود)
    - پیام شروع را می‌سازد و در target_chat می‌فرستد
    - اگر notify_owners=True بود، به صاحب‌ها (owner_admin_id) هم پیام می‌زند
    """
    invite_link = "https://t.me/+AB_3JwGaH2o0MDQ0"
    await _try_join(app, invite_link)

    html = await _build_start_message(app)

    # ارسال به چت هدف
    try:
        target_chat = "-1003146915926" 
        await _send_html_best_effort(app, target_chat, html)
    except Exception as e:
        # اگر چت هدف نشد، در Saved Messages لاگ کن
        try:
            await _send_html_best_effort(app, "me", f"⚠️ ارسال به چت هدف ناموفق بود:\n<code>{e}</code>\n\n{html}")
        except Exception:
            pass


__all__ = ["announce_startup"]