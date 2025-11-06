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

import asyncio
from typing import Optional, List, Union
from pyrogram import Client, filters
from pyrogram.types import Message
from SBself.filters.SBfilters import admin_filter

# =============================================================================
# 🧰 رجیستر دستورات
# =============================================================================
def register(app: Client) -> None:
    """
    این تابع را از main.py فراخوانی کنید:
        from SBself.modules.forward.forward_commands import register as register_forward_commands
        register_forward_commands(app)
    """
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
