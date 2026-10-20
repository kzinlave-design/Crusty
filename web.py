import os
import asyncio
import threading
from aaa import web_app, main

_bot_thread_started = False

def _start_bot():
    global _bot_thread_started
    if _bot_thread_started:
        return
    _bot_thread_started = True
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Bot crashed: {e}")

# Запускаем бота в фоне при старте gunicorn
threading.Thread(target=_start_bot, daemon=True).start()

# Этот блок нужен ТОЛЬКО для локального теста (python web.py)
# На Render он не сработает, так как gunicorn импортирует web_app напрямую
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
