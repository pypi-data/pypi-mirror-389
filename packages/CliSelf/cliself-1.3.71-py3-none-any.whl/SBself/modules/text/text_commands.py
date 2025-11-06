
# -*- coding: utf-8 -*-
# File: CliSelf/SBself/moudels/text/text_commands.py
#
# مدیریت کامل متن‌ها: افزودن خطی/انبوه، حذف، پاکسازی، دریافت همه، فول‌تکست، کپشن.
# استفاده در main.py:
#   from SBself.moudels.text.text_commands import register as register_text_commands
#   register_text_commands(app)

from __future__ import annotations

from pyrogram import Client, filters
from pyrogram.types import Message
from SBself.filters.SBfilters import admin_filter
from SBself.config import AllConfig
from pathlib import Path
import sys 

def build_caption(file_path: str, total_lines: int) -> str:
    fname = file_path.split("/")[-1] 
    return (
        f"«{fname}» ارسال شد ✅\n"
        f"تعداد خطوط: {total_lines}\n" 
    )
# --------------- Storage (AllConfig["text"]) ---------------
text_cfg = AllConfig.setdefault("text", {})
text_cfg.setdefault("lines", []) 
text_cfg.setdefault("caption", "")

# --------------- Business functions ---------------
async def text_add_line(txt: str) -> str:
    txt = (txt or "").strip()
    if not txt:
        return "❌ متن خالی است."
    text_cfg["lines"].append(txt)
    return f"✅ یک خط جدید اضافه شد. (مجموع: {len(text_cfg['lines'])})"

async def text_add_bulk(txt: str) -> str:
    raw = (txt or "").strip()
    if not raw:
        return "❌ متنی برای اضافه‌کردن نیست."
    lines = [t.strip() for t in raw.split('\n') if t.strip()]
    if not lines:
        return "❌ هیچ خط معتبری پیدا نشد."
    text_cfg["lines"].extend(lines)
    return f"✅ {len(lines)} خط اضافه شد. مجموع: {len(text_cfg['lines'])}"

async def text_del_line(txt: str) -> str:
    key = (txt or "").strip()
    if not key:
        return "❌ ورودی خالی است."
    try:
        text_cfg["lines"].remove(key)
        return "🗑 متن حذف شد."
    except ValueError:
        return "ℹ️ این متن در لیست نبود."
    except KeyError:
        return "ℹ️ لیست متن خالی است."

async def text_clear_all() -> str:
    text_cfg["lines"] = []
    return "🧹 تمام متن‌ها پاک شدند."

def _callsite_dir() -> Path:
    """
    مسیر پوشه‌ی اسکریپت اجراکننده (main.py).
    اگر در محیطی اجرا شد که __file__ ندارد (مثل REPL)،
    برمی‌گردد به پوشه‌ی کاری فعلی (cwd).
    """
    main_mod = sys.modules.get('__main__')
    if main_mod and getattr(main_mod, '__file__', None):
        return Path(main_mod.__file__).resolve().parent 
    
    return Path.cwd()
def write_numbered_lines(subdir: str = "downloads",filename: str = "text_file.txt") -> Path:
    lines = text_cfg.get("lines", [])
    output = "لیست متن خالی است." if not lines else "\n".join(
        f"{i+1}. {line}" for i, line in enumerate(lines)
    )

    base_dir = _callsite_dir()              
    target_dir = base_dir / subdir          
    target_dir.mkdir(parents=True, exist_ok=True)

    file_path = target_dir / filename       # .../downloads/text_file.txt

    # "w" ⇒ هر بار رونویسی
    with file_path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text_get_all())

    return file_path  # مسیر نهایی فایل را برمی‌گرداند

def text_get_all() -> str:
    lines = text_cfg.get("lines", [])
    if not lines:
        return "لیست متن خالی است."
    # خروجی شماره‌گذاری‌شده
    return "\n".join(f"{i+1}. {line}" for i, line in enumerate(lines))

def get_downloads_file(filename: str = "text_file.txt") -> Path:
    # پوشه‌ی کنار main.py
    main_mod = sys.modules.get('__main__')
    if main_mod and getattr(main_mod, '__file__', None):
        base_dir = Path(main_mod.__file__).resolve().parent
    else:
        base_dir = Path.cwd()
    return base_dir / "downloads" / filename

async def set_full_text(txt: str) -> str:
    text_cfg["lines"].append(txt)
    return "📜 متن کامل (fulltext) تنظیم شد."

async def set_caption(txt: str) -> str:
    text_cfg["caption"] = txt or ""
    return "💬 کپشن جدید تنظیم شد."

async def clear_caption() -> str:
    text_cfg["caption"] = ""
    return "🧹 کپشن پاک شد."

async def get_caption() -> str:
    val = text_cfg.get("caption", "")
    return val if val else "کپشنی تنظیم نشده است."

# --------------- Register handlers ---------------
def register(app: Client) -> None:
    @app.on_message(admin_filter & filters.command("text", prefixes=["/", ""]))
    async def _text_add(client: Client, m: Message):
        txt = m.text.split(None, 1)[1] if (m.text and len(m.command) > 1) else ""
        await m.reply(await text_add_line(txt))

    @app.on_message(admin_filter & filters.command("textall", prefixes=["/", ""]))
    async def _text_all(client: Client, m: Message):
        txt = m.text.split(None, 1)[1] if (m.text and len(m.command) > 1) else ""
        await m.reply(await text_add_bulk(txt))

    @app.on_message(admin_filter & filters.command("deltext", prefixes=["/", ""]))
    async def _text_del(client: Client, m: Message):
        txt = m.text.split(None, 1)[1] if (m.text and len(m.command) > 1) else ""
        await m.reply(await text_del_line(txt))

    @app.on_message(admin_filter & filters.command("cls_text", prefixes=["/", ""]))
    async def _text_clear(client: Client, m: Message):
        await m.reply(await text_clear_all())

    @app.on_message(admin_filter & filters.command("gettext", prefixes=["/", ""]))
    async def _gettext(client: Client, m: Message):
        write_numbered_lines() 
        file_path = get_downloads_file()  # .../downloads/text_file.txt
        total_lines = sum(1 for _ in open(file_path, "r", encoding="utf-8"))
        caption = build_caption(str(file_path), total_lines)
        await client.send_document(
            chat_id=m.chat.id,
            document=str(file_path),
            caption=caption)

    @app.on_message(admin_filter & filters.command("fulltext", prefixes=["/", ""]))
    async def _fulltext_set(client: Client, m: Message):
        txt = m.text.split(None, 1)[1] if (m.text and len(m.command) > 1) else ""
        await m.reply(await set_full_text(txt))

    @app.on_message(admin_filter & filters.command("caption", prefixes=["/", ""]))
    async def _cap_set(client: Client, m: Message):
        txt = m.text.split(None, 1)[1] if (m.text and len(m.command) > 1) else ""
        await m.reply(await set_caption(txt))

    @app.on_message(admin_filter & filters.command("cls_caption", prefixes=["/", ""]))
    async def _cap_clear(client: Client, m: Message):
        await m.reply(await clear_caption())

    @app.on_message(admin_filter & filters.command("getcap", prefixes=["/", ""]))
    async def _cap_get(client: Client, m: Message):
        await m.reply(await get_caption())
