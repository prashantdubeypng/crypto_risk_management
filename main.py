# main.py
import asyncio
import nest_asyncio
from TeligramBot.teligram_bot import run_bot

nest_asyncio.apply()  # 👈 Add this line to allow reusing the event loop

if __name__ == "__main__":
    asyncio.run(run_bot())
