import os
import asyncio
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    Application,
)

from TeligramBot import handlers
from TeligramBot.handlers import start, monitor_risk, hedge_now, button_callback
from riskEngine.monitor import check_user_risks

"""
This module initializes and runs a Telegram bot designed for cryptocurrency risk
management. It sets up command handlers for user interactions (e.g., starting
monitoring, hedging, viewing analytics) and incorporates a background task
to periodically check user asset risks and trigger alerts or auto-hedging.
"""

# Load environment variables from a .env file.
load_dotenv()
# Retrieve the Telegram bot API token from environment variables.
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def setup_handlers(app: Application):
    """
    Sets up all command and callback query handlers for the Telegram bot.

    Args:
        app (Application): The Telegram bot application instance to which
                           handlers will be added.
    """
    # Register command handlers for various user commands.
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("predict_Bitcoin_price",handlers.predict_btc_handler))
    app.add_handler(CommandHandler("monitor_risk", monitor_risk))
    app.add_handler(CommandHandler("auto_hedge", handlers.auto_hedge))
    app.add_handler(CommandHandler("hedge_now", handlers.hedge_now))
    app.add_handler(CommandHandler("View_full_analytics", handlers.full_analytics))
    app.add_handler(CommandHandler("update_threshold", handlers.update_threshold))
    app.add_handler(CommandHandler("stop_monitor_risk", handlers.Stop_monitor))
    app.add_handler(CommandHandler("disable_auto_hedge", handlers.disable_auto_hedge))
    # Register a callback query handler for inline keyboard button presses.
    app.add_handler(CallbackQueryHandler(button_callback))


async def run_risk_monitor(app: Application):
    """
    Asynchronously runs a periodic background task to check user risks.

    This function continuously calls `check_user_risks` at a fixed interval
    (every 60 seconds) to monitor all active user positions for risk.

    Args:
        app (Application): The Telegram bot application instance, used to
                           access the bot object (`app.bot`) for sending messages.
    """
    while True:
        # Call the risk checking function, passing the bot object.
        await check_user_risks(app.bot)
        # Pause execution for 60 seconds before the next check.
        await asyncio.sleep(60)


async def run_bot():
    """
    Initializes and starts the Telegram bot, including its command handlers
    and the background risk monitoring task.
    """
    # Build the Telegram Application instance using the provided API token.
    app = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    # Set up all the command and callback handlers.
    setup_handlers(app)

    # Create and run the background risk monitor task.
    # This task will run concurrently with the bot's polling.
    app.create_task(run_risk_monitor(app))

    print("🤖 Telegram bot is running...")
    # Start polling for updates from Telegram, keeping the bot running.
    await app.run_polling()