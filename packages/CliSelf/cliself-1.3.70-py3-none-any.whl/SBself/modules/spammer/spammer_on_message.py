# -*- coding: utf-8 -*-
import asyncio
import inspect
from typing import Optional, Callable, Any, Dict

from ...config import AllConfig
from ...core.utils import maybe_typing
from ...core.final_text import build_final_text

# اشاره به خودِ تابع (فراخوانی نکن!)
_final_text_fn: Optional[Callable[..., str]] = build_final_text

# پیش‌فرض‌های امنِ کانفیگ
_spam_defaults: Dict[str, Any] = {
    "run_kill": False,
    "typing_on": False,
    "time": 1,          # حداقل ۱ ثانیه تاخیر پیش‌فرض
}
AllConfig.setdefault("spammer", {}).update({k: AllConfig["spammer"].get(k, v) for k, v in _spam_defaults.items()})


async def _call_maybe_async(func: Callable, *args, **kwargs):
    """اجرای امن برای تابع sync/async."""
    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)


def _get_spammer_cfg() -> Dict[str, Any]:
    """هر بار ریفرنس تازه از کانفیگ برگردان (تا اگر جای دیگر جایگزین شد، اینجا قدیمی نماند)."""
    return AllConfig.setdefault("spammer", {})


def _safe_delay_seconds(val: Any) -> int:
    """تاخیر امن: هر ورودی نامعتبر → 1 ثانیه."""
    try:
        sec = int(val)
    except Exception:
        sec = 1
    return 1 if sec < 1 else sec


async def start_kill(client, chat_id: int, reply_id: int) -> None:
    # روشن کردن فلگ روی خودِ AllConfig (نه یک ریفرنس قدیمی)
    _get_spammer_cfg()["run_kill"] = True

    while _get_spammer_cfg().get("run_kill", False):
        try:
            # ۱) تولید متن نهایی
            if _final_text_fn is None or not callable(_final_text_fn):
                print("Text builder not available.")
                await asyncio.sleep(1)
                continue

            try:
                text = _final_text_fn()
            except TypeError:
                # نسخه‌های خیلی قدیمی اگر آرگومان می‌خواستند، None بدهیم
                text = _final_text_fn(None)  # type: ignore

            if not text:
                # متن خالی؛ یک مکث کوتاه و تلاش دوباره
                await asyncio.sleep(1)
                continue

            # ۲) تایپینگ اختیاری
            s = _get_spammer_cfg()  # تازه‌خوانی
            if s.get("typing_on", False):
                try:
                    await _call_maybe_async(maybe_typing, client, chat_id, 2)
                except Exception:
                    pass  # تایپینگ اگر شکست بخورد، ارسال پیام را متوقف نکن

            # ۳) ارسال پیام (با HTML چون خروجی نهایی منشن HTML دارد)
            try:
                await client.send_message(
                    chat_id,
                    text,
                    reply_to_message_id=reply_id, 
                    disable_web_page_preview=True,
                )
            except Exception as send_err:
                print(f"send_message error: {send_err}")
                # خطا در ارسال؛ کمی صبر و ادامه
                await asyncio.sleep(1)

            # ۴) تاخیر
            s = _get_spammer_cfg()  # دوباره تازه بگیر
            delay = _safe_delay_seconds(s.get("time", 1))
            # اگر حین تاخیر فلگ خاموش شد، سریع خارج شویم
            for _ in range(delay):
                if not _get_spammer_cfg().get("run_kill", False):
                    break
                await asyncio.sleep(1)

        except Exception as e:
            print(f"Error in kill loop: {e}")
            await asyncio.sleep(1)

    # خروج تمیز
    print("kill loop exited.")


async def stop_kill() -> str:
    _get_spammer_cfg()["run_kill"] = False
    return "عملیات متوقف شد."
