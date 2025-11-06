# -*- coding: utf-8 -*-
# File: SBself/config.py
#
# ⚙️ پیکربندی مرکزی برنامه
# - از این نسخه، «تکست‌ها» در AllConfig["text"]["lines"] نگهداری می‌شوند
# - نیازی به فایل downloads/text.txt نیست
# - هِلپر اختیاری migrate_legacy_texts برای انتقال یک‌باره از فایل قدیمی فراهم شده

import os
from typing import List, Dict, Any

# ---------------------------
# 👥 لیست ادمین‌ها
# ---------------------------
adminList = [5053851121]

# ---------------------------
# 🧠 تنظیمات کلی اپلیکیشن
# ---------------------------
app_config: Dict[str, Any] = {
    "name": "app",
    "api_id": 17221354,
    "api_hash": "b86bbf4b700b4e922fff2c05b3b8985f",
}

# ---------------------------
# 💬 اسپمر و پیام‌رسانی خودکار
# ---------------------------
spammer_config: Dict[str, Any] = { 
    "time": 10,
    "run_spammer": False,
    "run_kill": False,
    "typing_on": False,
    "sent_count":0,
    "error_count":0,
    "targets": [],  
}

# ---------------------------
# 🧍‍♂️ تنظیمات منشن‌ها
# ---------------------------
mention_config: Dict[str, Any] = {
    "textMen": "",
    "useridMen": "",
    "is_menshen": False,
    "group_menshen": False,
    "group_ids": [],
}

# ---------------------------
# 😡 دشمن‌ها و mute
# ---------------------------
enemy_config: Dict[str, Any] = {
    "enemy": [],
    "special_enemy": [],
    "enemy_ignore": 0,
    "enemy_counter": {},
    "mute": [],
    "specialenemytext": [],
    "SPTimelist": [],
}

# ---------------------------
# 👮‍♂️ ادمین‌ها
# ---------------------------
admin_config: Dict[str, Any] = {
    "admins": [5053851121],
}

# ---------------------------
# 📝 تغییر نام خودکار
# ---------------------------
names_config: Dict[str, Any] = {
    "names": [],
    "change_interval_h": 1,
    "changenames": False,
    "changenames_idx": 0,
    "changenames_task": None,
}

# ---------------------------
# 💾 بکاپ و پایگاه داده
# ---------------------------
backup_config: Dict[str, Any] = {
    "bk_enabled": True,
    "bk_db": "downloads/backup.db",
    "bk_dir": "downloads/bk_exports",
    "bk_wipe_threshold": 10,
    "bk_wipe_window_minutes": 1,   # پنجرهٔ شمارش حذف‌ها برای تشخیص wipe
    "bk_cooldown_minutes": 1,      # کول‌داون برای جلوگیری از اسپم بکاپ
}

# ---------------------------
# 📷 تنظیمات مدیا
# ---------------------------
media_config: Dict[str, Any] = {
    "catch_view_once": True,
}

# ---------------------------
# ⏱ تایمر پیام‌ها
# ---------------------------
timer_config: Dict[str, Any] = {
    "text": "",
    "time": 0,
    "chat_id": None,
    "first_time": None,
    "last_interval": 0,
    "repeat": 100,
    "message_ids": [],
    "is_running": False,
    "auto": False,
    "targets": [],  
}

# ---------------------------
# 🧾 متن‌ها (جایگزین فایل text.txt)
# --------------------------- 
text_config: Dict[str, Any] = {
    "lines": [],   # لیست رشته‌ها
    "caption":"",
}

# فقط همین دیکشنری؛ هر تغییری بدی در runtime توسط منیجر اعمال میشه.
ANTI_LOGIN_CONFIG = {
    "anti_login": False,   # on/off
    "target_sender": None, # int user_id یا str یوزرنیم (بدون @)
} 

# ---------------------------
# ⚙️ ترکیب همه‌ی تنظیمات در AllConfig
# ---------------------------
AllConfig: Dict[str, Any] = {
    "app": app_config,
    "spammer": spammer_config,
    "mention": mention_config,
    "enemy": enemy_config,
    "admin": admin_config,
    "names": names_config,
    "backup": backup_config,
    "media": media_config,
    "timer": timer_config,
    "text": text_config,       # ← مهم: بخش جدید متن‌ها
    "anti_login":ANTI_LOGIN_CONFIG,
    "owners": []
}

from copy import deepcopy

# یک اسنپ‌شات از پیش‌فرض‌ها در لحظهٔ import
_DEFAULTS = {
    "app": deepcopy(app_config),
    "spammer": deepcopy(spammer_config),
    "mention": deepcopy(mention_config),
    "enemy": deepcopy(enemy_config),
    "admin": deepcopy(admin_config),
    "names": deepcopy(names_config),
    "backup": deepcopy(backup_config),
    "media": deepcopy(media_config),
    "timer": deepcopy(timer_config),
    "text": deepcopy(text_config),
    "owners": [],  # پیش‌فرض خالی؛ در ریست مقدار فعلی owners را حفظ می‌کنیم
}

def reset_state_preserve_admins_owners() -> None:
    """
    همه‌چیز را به پیش‌فرض برگردان، بجز:
      - admin_config["admins"]
      - AllConfig["owners"]
    """
    global AllConfig, app_config, spammer_config, mention_config, enemy_config
    global admin_config, names_config, backup_config, media_config, timer_config
    global text_config

    current_admins = list(admin_config.get("admins", []))
    current_owners = list(AllConfig.get("owners", []))

    def _apply(section: str, ref_name: str):
        new_val = deepcopy(_DEFAULTS[section])
        globals()[ref_name].clear()
        globals()[ref_name].update(new_val)
        AllConfig[section] = globals()[ref_name]

    _apply("app",     "app_config")
    _apply("spammer", "spammer_config")
    _apply("mention", "mention_config")
    _apply("enemy",   "enemy_config")
    _apply("admin",   "admin_config")
    _apply("names",   "names_config")
    _apply("backup",  "backup_config")
    _apply("media",   "media_config")
    _apply("timer",   "timer_config")
    _apply("text",    "text_config")

    admin_config["admins"] = current_admins
    AllConfig["admin"] = admin_config

    AllConfig["owners"] = current_owners 

def _reset_state_to_defaults():
    try:
        reset_state_preserve_admins_owners()
        return "♻️ Restarting complete"
    except Exception as e:
        return f"Error to Restarting\nerror :{e}"