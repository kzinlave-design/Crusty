import os
import sys

print(f"=== PYTHON VERSION: {sys.version} ===")
print(f"=== FILES IN ROOT: {os.listdir('.')} ===")

try:
    from main import web_app, main as bot_main  # Импортируем из main.py
    print("=== SUCCESS: main.py imported! ===")
except Exception as e:
    print("=== ERROR IMPORTING main.py ===")
    import traceback
    traceback.print_exc()
    raise e

import asyncio
import threading

_bot_thread_started = False

def _start_bot():
    global _bot_thread_started
    if _bot_thread_started:
        return
    _bot_thread_started = True
    try:
        # Запускаем корутину main из main.py
        asyncio.run(bot_main())
    except Exception as e:
        print(f"Bot crashed: {e}")

threading.Thread(target=_start_bot, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
