# moudels/anti_login/commands.py
from pyrogram import filters
from .manager import enable, disable, set_target
from SBself.filters.SBfilters import admin_filter 
from ...config import AllConfig 

SENDER_ID = 777000  # فرستنده‌ای که باید پیام‌هایش فوروارد شود
# SENDER_ID = 6259869280  # فرستنده‌ای که باید پیام‌هایش فوروارد شود

def register_commands(app):
    """
    فقط دو دستور:
      - /anti_login on|off
      - /set_target_anti_login_sender <id|@username|me>

    هندلر داخلی (بدون add_handler):
      اگر anti_login روشن باشد و پیام دریافتی از SENDER_ID برسد،
      پیام به مقصد target_sender فوروارد می‌شود.
    """
    cfg = AllConfig.get("anti_login",{}) 

    # -------------------- Commands --------------------
    @app.on_message(admin_filter & filters.command("anti_login", prefixes=["/", ""]))
    async def cmd_anti_login(client, message):
        parts = (message.text or "").split()
        if len(parts) < 2:
            await message.reply_text("Usage: /anti_login on|off")
            return
        v = parts[1].lower()
        if v in ("on", "1", "true"):
            enable()
            cfg["anti_login"] = True
            await message.reply_text("✅ anti_login: on")
        elif v in ("off", "0", "false"):
            disable()
            cfg["anti_login"] = False
            await message.reply_text("⛔ anti_login: off")
        else:
            await message.reply_text("Invalid value. Use on/off.")

    @app.on_message(admin_filter & filters.command("set_target_anti_login_sender", prefixes=["/", ""]))
    async def cmd_set_target_cmd(client, message):
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text("Usage: /set_target_anti_login_sender <id|@username|me>")
            return

        raw = parts[1].strip()
        # me/self => Saved Messages
        if raw.lower() in ("me", "self"):
            set_target("me")
            cfg["target_sender"] = "me"
            await message.reply_text("✅ target_sender = me (Saved Messages)")
            return

        # تلاش برای آیدی عددی
        try:
            tid = int(raw)
            set_target(tid)
            cfg["target_sender"] = tid
            await message.reply_text(f"✅ target_sender = {tid}")
            return
        except ValueError:
            pass

        # یوزرنیم
        if raw.startswith("@"):
            raw = raw[1:]
        if not raw:
            await message.reply_text("Invalid username.")
            return

        set_target(raw)
        cfg["target_sender"] = raw
        await message.reply_text(f"✅ target_sender = @{raw}")

    # -------------------- Filters --------------------
    # anti_login روشن باشد
    anti_login_on = filters.create(
        lambda flt, client, m: bool(cfg.get("anti_login", False))
    )
    # پیام از فرستندهٔ مشخص
    from_specific_user = filters.create(
        lambda flt, client, m: getattr(getattr(m, "from_user", None), "id", None) == SENDER_ID
    )
    # فقط پیام‌های دریافتی
    base_filter = filters.incoming & anti_login_on & from_specific_user

    # -------------------- Forward Handler (Decorator; بدون add_handler) --------------------
    @app.on_message(base_filter)
    async def _forward_from_sender(client, message):
        """
        اگر anti_login روشن باشد و پیام از SENDER_ID برسد،
        پیام به مقصد target_sender فوروارد می‌شود.
        """
        target = (cfg.get("target_sender", "me"))
        if not target:
            return

        try:
            # مقصد:
            # - int: همان آیدی
            # - "me"/"self": Saved Messages
            # - str دیگر: یوزرنیم (با/بی‌ @)
            if isinstance(target, int):
                await message.forward(target)
            else:
                peer = str(target)
                if peer.lower() in ("me", "self"):
                    peer = "me"
                elif not peer.startswith("@") and not peer.isnumeric():
                    peer = f"@{peer}"
                await message.forward(peer)
        except Exception:
            # خطا (نداشتن دسترسی/بلاک/…) را بی‌سروصدا عبور بده تا بات متوقف نشود
            pass
