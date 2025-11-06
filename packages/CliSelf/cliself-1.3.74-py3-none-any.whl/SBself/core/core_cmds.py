# -*- coding: utf-8 -*-
# File: CliSelf/SBself/core/core_cmds.py
# -*- coding: utf-8 -*-
# File: CliSelf/SBself/core/core_cmds.py
"""
Ultra-Status v7 — نسخه فارسی، فقط وضعیت کلی و قابلیت‌ها

✅ کاملاً فارسی
✅ حذف سیستم و شبکه
✅ نمایش جزئیات کامل قابلیت‌ها
"""

import os, sys, time, json, asyncio, locale, socket, platform
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore

try:
    from pyrogram import Client
except Exception:
    Client = None  # type: ignore

from ..config import AllConfig, _reset_state_to_defaults

START_TIME = time.time()
# =============================
# 🧰 Core commands
# =============================

async def ping(client: Optional[Client]=None, chat_id: Optional[int]=None) -> str:
    t0=time.perf_counter()
    api_ms=None
    try:
        if client: 
            await client.get_me()
            api_ms=(time.perf_counter()-t0)*1000
    except Exception: pass
    parts=["PONG"]
    if api_ms: parts.append(f"\n• API: {api_ms:.0f} ms")
    return "".join(parts)

async def uptime() -> str:
    return f"⏱ Uptime: {_human_dt(time.time()-START_TIME)}"

async def restart() -> str:
    try: return _reset_state_to_defaults()
    except Exception as e: return f"⚠️ Restart error: {e}"

async def shutdown() -> str:
    os._exit(0)


# =============================
# 🔧 ابزارهای کمکی
# =============================

def _human_dt(seconds: float) -> str:
    if seconds < 0: seconds = 0
    d, rem = divmod(int(seconds), 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    return f"{d}d {h:02}h {m:02}m {s:02}s" if d else f"{h:02}h {m:02}m {s:02}s"

def _fmt_bool(x): return "✅ فعال" if bool(x) else "❌ غیرفعال"

def _fmt_bytes(n: Optional[float]) -> str:
    if n is None: return "—"
    for u in ["B","KB","MB","GB","TB"]:
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"

def _safe_get(d, k, default=None):
    try: return d.get(k, default)
    except Exception: return default

def _truncate_list(items: List[Any], limit=5) -> str:
    if not items: return "—"
    items=list(items)
    return ", ".join(map(str, items[:limit])) + (f" و {len(items)-limit} مورد دیگر" if len(items)>limit else "")

# =============================
# 🧠 اطلاعات پایه
# =============================

def _collect_environment() -> List[Tuple[str,str]]: 
    sys_ver = f"{platform.system()} {platform.release()}"
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return [ 
        ("سیستم‌عامل", sys_ver),
        ("نسخه پایتون", py_ver),
        ("زمان اجرا", _human_dt(time.time() - START_TIME)),
    ]

# =============================
# ⚙️ قابلیت‌ها
# =============================

def _collect_features(cfg: Dict[str, Any]) -> List[Tuple[str, str]]:
    spammer = cfg.get("spammer", {})
    spam_msg = cfg.get("spammer_msg", {})
    timer = cfg.get("timer", {})
    enemy = cfg.get("enemy", {})
    rename = cfg.get("rename_scheduler", {})
    backup = cfg.get("backup", {}) 

    rows: List[Tuple[str,str]] = []

    # 🎯 اسپمر کلی
    rows.append(("اسپمر", _fmt_bool(spammer.get("enabled", False)))) 
    rows.append(("تعداد ارسال موفق", str(spammer.get("sent_count", 0))))
    rows.append(("تعداد خطا", str(spammer.get("error_count", 0))))
    rows.append(("سرعت ارسال", f"{spammer.get('time', 0)} ثانیه"))

    # 💬 اسپمر پیام
    rows.append(("اسپمر روی پیام", _fmt_bool(spam_msg.get("enabled", False))))
    rows.append(("حالت تایپ در اسپمر روی پیام", _fmt_bool(spam_msg.get("typing_on", False))))

    # ⏰ تایمر
    rows.append(("تایمر", _fmt_bool(timer.get("is_running", False))))
    rows.append(("اتوماتیک", _fmt_bool(timer.get("auto", False))))
    rows.append(("زمان (ثانیه)", str(timer.get("time", 0))))
    rows.append(("زمان (دقیقه)", str(round(timer.get("time", 0) / 60, 2))))
    rows.append(("هدف‌ها", _truncate_list(timer.get("targets", []))))
    rows.append(("متن", timer.get("text", "—")))
    rows.append(("حداکثر تکرار", str(timer.get("repeat", 0))))
    rows.append(("شناسه چت", str(timer.get("chat_id", "—"))))
    rows.append(("اولین اجرا", str(timer.get("first_time", "—"))))
    rows.append(("آخرین فاصله", str(timer.get("last_interval", 0)))) 
    # محاسبه اجرای بعدی
    _next_run = "—"
    first_time = timer.get("first_time")
    if isinstance(first_time, datetime):
        _next_run = first_time + timedelta(seconds=timer.get("last_interval", 0) + timer.get("time", 0))
    elif isinstance(first_time, str) and first_time not in [None, "—"]:
        try:
            t = datetime.fromisoformat(first_time)
            _next_run = t + timedelta(seconds=timer.get("last_interval", 0) + timer.get("time", 0))
        except ValueError:
            _next_run = "—"
    rows.append(("اجرای بعدی", str(_next_run)))

    # ⚔️ دشمن و دشمن ویژه
    rows.append(("دشمن معمولی", _fmt_bool(bool(enemy.get("enemy")))))
    rows.append(("تعداد دشمن‌ها", str(len(enemy.get("enemy", [])))))
    rows.append(("دشمن ویژه", _fmt_bool(bool(enemy.get("special_enemy")))))
    rows.append(("تعداد دشمن‌های ویژه", str(len(enemy.get("special_enemy", [])))))
    rows.append(("لیست بی‌صداها (Mute)", str(len(enemy.get("mute", [])))))
    rows.append(("متن دشمن ویژه‌ها", _truncate_list(enemy.get("specialenemytext", []))))
    rows.append(("لیست زمان‌های ویژه (SPTimelist)", _truncate_list(enemy.get("SPTimelist", []))))
    rows.append(("تعداد شمارنده دشمن‌ها", str(len(enemy.get("enemy_counter", {})))))
    rows.append(("تعداد دشمن‌های نادیده‌گرفته‌شده", str(enemy.get("enemy_ignore", 0))))

    # 🔄 تغییر نام زمان‌بندی‌شده
    rows.append(("تغییر نام زمان‌بندی‌شده", _fmt_bool(rename.get("changenames", False))))
    rows.append(("فاصله تغییر نام (ساعت)", str(rename.get("change_interval_h", 0))))
    rows.append(("تعداد نام‌ها", str(len(rename.get("names", [])))))
    rows.append(("ایندکس فعلی نام", str(rename.get("changenames_idx", 0))))
    rows.append(("تسک فعال تغییر نام", str(rename.get("changenames_task", "—"))))

    # محاسبه زمان اجرای بعدی بر اساس فاصله ساعت
    _next_run = "—"
    if rename.get("changenames_task"): 
        _next_run = datetime.now() + timedelta(hours=rename.get("change_interval_h", 0))

    rows.append(("زمان اجرای بعدی تغییر نام", str(_next_run)))

    # 💾 بک‌آپ
    rows.append(("پشتیبان‌گیری فعال", _fmt_bool(backup.get("bk_enabled", False))))
    rows.append(("مسیر فایل دیتابیس", backup.get("bk_db", "—")))
    rows.append(("محل ذخیرهٔ خروجی‌ها", backup.get("bk_dir", "—")))
    rows.append(("حد آستانهٔ حذف‌ها (wipe_threshold)", str(backup.get("bk_wipe_threshold", 0))))
    rows.append(("پنجرهٔ زمانی تشخیص حذف (دقیقه)", str(backup.get("bk_wipe_window_minutes", 0))))
    rows.append(("زمان کول‌داون (دقیقه)", str(backup.get("bk_cooldown_minutes", 0))))
    return rows

# =============================
# 🎨 خروجی کاربر پسند (فقط فارسی)
# =============================

def _pair(k, v): return f"• {k}: {v}"

def _render_human(cfg: Dict[str,Any]) -> str:
    env = _collect_environment()
    feats = _collect_features(cfg)

    parts = ["> وضعیت کلی برنامه\n"]
    parts += [_pair(k,v) for k,v in env]
    # parts.append("\n# قابلیت‌ها\n")
    parts += [_pair(k,v) for k,v in feats]

    return "\n".join(parts).strip()

# =============================
# 🧾 STATUS
# =============================

async def status(audience: str = "human") -> str:
    cfg = AllConfig
    if audience == "human":
        return _render_human(cfg)
    else:
        return json.dumps({
            "Environment": dict(_collect_environment()),
            "Features": dict(_collect_features(cfg))
        }, ensure_ascii=False, indent=2)

# =============================
# 📖 HELP
# =============================

async def help_text() -> str:
    return (
        "📖 راهنمای دستورات:\n"
        "- status → نمایش وضعیت کلی و قابلیت‌ها\n"
        "- ping → تست اتصال\n"
        "- uptime → زمان اجرای برنامه\n"
        "- restart → بازنشانی وضعیت\n"
        "- shutdown → خاموش کردن برنامه\n"
    )
