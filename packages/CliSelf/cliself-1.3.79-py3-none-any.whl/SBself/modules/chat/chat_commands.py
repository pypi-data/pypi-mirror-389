# -*- coding: utf-8 -*-
# File: SBself/moudels/chat/chat_commands.py
#
# دستورات مدیریت چت‌ها: join / left / delall / del
# استفاده در main.py:
#   from SBself.moudels.chat.chat_commands import register as register_chat_commands
#   register_chat_commands(app)

import logging
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import Message

from SBself.filters.SBfilters import admin_filter

# بیزنس‌لاجیک‌ها
from .chat_manager import ChatManager
from .chat_cleaner import ChatCleaner

logger = logging.getLogger(__name__)

# سرویس‌های singleton برای طول اجرای برنامه
_chat_manager: Optional[ChatManager] = None
_chat_cleaner: Optional[ChatCleaner] = None


def _ensure_services(app: Client) -> None:
    """
    اطمینان از مقداردهی تنبلِ سرویس‌ها.
    """
    global _chat_manager, _chat_cleaner
    if _chat_manager is None:
        _chat_manager = ChatManager(app)
        logger.info("ChatManager initialized")
    if _chat_cleaner is None:
        _chat_cleaner = ChatCleaner(app)
        logger.info("ChatCleaner initialized")


# --------------------- Wrapper funcs (safe replies) ---------------------
async def join_chat(target: str) -> str:
    try:
        # type: ignore[attr-defined] چون مقداردهی تنبل انجام شده
        return await _chat_manager.join_chat(target)  # type: ignore[attr-defined]
    except ValueError as e:
        return f"❌ {e}"
    except TimeoutError as e:
        return f"⏰ {e}"
    except PermissionError as e:
        return f"🔒 {e}"
    except Exception as e:
        return f"⚠️ Join failed: {e}"


async def leave_chat(identifier: str) -> str:
    try:
        return await _chat_manager.leave_chat(identifier)  # type: ignore[attr-defined]
    except Exception as e:
        return f"⚠️ Leave failed: {e}"


async def clear_all(chat_id, title: Optional[str] = None) -> str:
    try:
        return await _chat_cleaner.clean_all(chat_id)  # type: ignore[attr-defined]
    except Exception as e:
        return f"⚠️ DelAll failed: {e}"


async def clear_last(chat_id, n: int) -> str:
    try:
        return await _chat_cleaner.del_last(chat_id, n)  # type: ignore[attr-defined]
    except Exception as e:
        return f"⚠️ DelLast failed: {e}"


# --------------------------- Register handlers ---------------------------
def register(app: Client) -> None:
    """
    رجیستر کردن هندلرهای دستورات:
      - join <invite|@username|chat_id>
      - left <@username|chat_id>
      - delall
      - del <N>
    با admin_filter محصور شده‌اند.
    """
    _ensure_services(app)

    @app.on_message(admin_filter & filters.command("join", prefixes=["/", ""]))
    async def _join(client: Client, m: Message):
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: join <link|@username|chat_id>")
        target = m.text.split(None, 1)[1]
        await m.reply(await join_chat(target))

    @app.on_message(admin_filter & filters.command("left", prefixes=["/", ""]))
    async def _left(client: Client, m: Message):
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: left <chat_id|@username>")
        await m.reply(await leave_chat(m.command[1]))

    @app.on_message(admin_filter & filters.command("delall", prefixes=["/", ""]))
    async def _delall(client: Client, m: Message):
        chat = m.chat
        chat_id = chat.id
        # نام قابل‌خواندن چت
        title = (
            getattr(chat, "title", None)
            or f"{getattr(chat, 'first_name', '')} {getattr(chat, 'last_name', '')}".strip()
            or str(chat_id)
        )
        await clear_all(chat_id)

    @app.on_message(admin_filter & filters.command("del", prefixes=["/", ""]))
    async def _deln(client: Client, m: Message):
        if not (m.text and len(m.command) > 1):
            return await m.reply("Usage: del <N>")
        try:
            # حداقل 1
            n = max(1, int(m.command[1]))
        except Exception:
            return await m.reply("❌ عدد معتبر بده.")
        # current_msg_id را پاس می‌دهیم تا پیام دستور خودش حذف نشود
        await clear_last(m.chat.id, n)
