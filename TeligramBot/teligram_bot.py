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

# Load .env
load_dotenv()
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Setup command and callback handlers
def setup_handlers(app: Application):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("monitor_risk", monitor_risk))
    app.add_handler(CommandHandler("auto_hedge", handlers.auto_hedge))
    app.add_handler(CommandHandler("hedge_now", handlers.hedge_now))
    app.add_handler(CommandHandler("View_full_analytics", handlers.full_analytics))
    app.add_handler(CommandHandler("update_threshold", handlers.update_threshold))
    app.add_handler(CommandHandler("stop_monitor_risk", handlers.Stop_monitor))
    app.add_handler(CommandHandler("disable_auto_hedge", handlers.disable_auto_hedge))
    app.add_handler(CallbackQueryHandler(button_callback))


# Periodic background task
async def run_risk_monitor(app: Application):
    while True:
        await check_user_risks(app.bot)
        await asyncio.sleep(60)  # run every 60 seconds


# Async bot runner with background task
async def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_API_TOKEN).build()

    setup_handlers(app)

    # Run background risk monitor task
    app.create_task(run_risk_monitor(app))

    print("🤖 Telegram bot is running...")
    await app.run_polling()
