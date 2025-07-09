# main.py
"""
Main entry point for the Telegram bot application.

This script initializes and starts the asynchronous Telegram bot.
It uses `nest_asyncio` to handle potential issues with nested event loops,
which can occur in certain environments (e.g., Jupyter notebooks, some IDEs)
where `asyncio.run()` might be called when an event loop is already running.
"""

import asyncio # Import the asyncio library for asynchronous programming.
import nest_asyncio # Import nest_asyncio to allow nested use of asyncio.run().
from TeligramBot.teligram_bot import run_bot # Import the main bot running function.

# Apply nest_asyncio. This line modifies the asyncio event loop policy
# to allow `asyncio.run()` to be called when an event loop is already running.
# This prevents `RuntimeError: This event loop is already running` in certain contexts.
nest_asyncio.apply()

# This block ensures that the run_bot() function is called only when the script is
# executed directly (not when imported as a module).
if __name__ == "__main__":
    # Run the main asynchronous bot function.
    # asyncio.run() manages the event loop for the asynchronous operations.
    asyncio.run(run_bot())