"""
Update: Represents an incoming update from Telegram (message, button click, etc.).
InlineKeyboardButton & InlineKeyboardMarkup: Used to create inline buttons inside a message (e.g., "Hedge Now").
CallbackContext: Stores context info during command execution (e.g., args, job queues).
ContextTypes: Used to get the default context type for type hinting in async handlers.
"""

# IMPORTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext import ContextTypes
import requests
from datetime import datetime
from exchanges.bybit import get_spot_price
from riskEngine.hedge import place_hedge_order

user_positions={} #--> Dictionary to save the user assets , position  , threshold
# --- Start command ---
async def start(update: Update, context: CallbackContext):
    user = update.effective_user # get the info of the user which is interacting to bot to just get more interaction
    message = ( #--> It is a message that going to be seen on the display
        f" Hello {user.first_name}!\n\n"
        "I'm your Crypto Risk Hedging Bot. Use the menu or commands below to get started:\n\n"
        " /monitor_risk <asset> <position_size> <risk_threshold>\n"
        "️ /auto_hedge <asset> @your hedge automatically started when threshold get trick of the monitor_risk \n"
        " /update_threshold <asset> <new threshold>\n"
        " /View_full_analytics <to get whole report about all assets\n"
        " /stop_monitor_risk <asset>\n"
        " /hedge_now <asset> <size>\n"
        " /disable_auto_hedge <asset>\n"
        " /hedge_history <asset> <timeframe>\n"
    )
    await update.message.reply_text(message) # it sends a message over the network , Without freezing
async def disable_auto_hedge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_positions:
        await update.message.reply_text("You have not yet start monitoring .")
        return
    try:
        if context.args:
            asset = context.args[0].upper()
            if asset in user_positions[user_id]:
                user_positions[user_id][asset]["auto_hedge"] = False
                await update.message.reply_text(f"Auto hedge disabled {asset}.")
            else:
                await update.message.reply_text(f"{asset} not in your holding yet update it.")
        else:
            for asset in user_positions[user_id]:
                user_positions[user_id][asset]["auto_hedge"] = False
    except Exception as e:
        await update.message.reply_text(f"Something went wrong. {e}")
async  def Stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_positions:
        await update.message.reply_text("🚫 You are not monitoring any assets.")
        return
    try:
        if context.args:
            asset = context.args[0].upper()
            if asset in user_positions[user_id]:
                del user_positions[user_id][asset]
                if not  user_positions[user_id]:
                    del user_positions[user_id]
                await update.message.reply_text("Stopped monitoring for {asset}.")
            else:
                await update.message.reply_text(" You are not monitoring any assets.")
        else:
          del user_positions[user_id]
          await update.message.reply_text("🛑 Stopped monitoring for all assets.")
    except Exception as e:
        await update.message.reply_text("❌ Failed to stop monitoring. Usage: /stop_monitor_risk <asset>")

    # --- Monitor command ---
    """
    This function is called when the bot receives a message from Telegram (message).
    To monitor _risk also when the user tricker it they have to give the input like asset name , size and threshold
    one command means user will upload one asset and its size and threshold 
    /monitor_risk <asset = BTC> <position_size=5 ---> how many BTC HAVE > <risk_threshold=20>
    if user have two asset they have to rerun monitor_risk command and have to input the data of second assets
    when user rerun the function for the second assent we have make an dictionary of the user.id that be the unique id 
    for the dictionary , so data is in one place and no duplicate data can be there 
    """
async def monitor_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id # get the user id of the user
        asset = context.args[0].upper() # we are saving the Keyword of the cryptocurrency in all letters in capital
        position_size = float(context.args[1]) # position size like how much that asset you have
        risk_threshold = float(context.args[2]) # how much loss you can beer and after get that threshold user get the notification
        current_price = get_spot_price(asset)
        if current_price is None:
            await update.message.reply_text("Failed to fetch current price for the asset.")
            return
        if user_id not in user_positions:
            user_positions[user_id] = {}
            """
            @ user_positions[user_id][asset] = {
            "position_size": position_size,
            "risk_threshold": risk_threshold,
        } 
        here we are saving the user data like assets , position size and risk threshold. , to check current price and also what 
        going to be in the future is user going to loss then we have to give him the @Alert
        we are creating  nested dictionary i.e means User_position={
        User_id :{
        BTC:{ # BTC is a asset 
        "position_size": position_size, #Position  for BTC 
        "risk_threshold": risk_threshold, # risk for BTC
        },
        ETH:{ # ETH is a asset 
        "position_size": position_size, # Position  for ETH 
        "risk_threshold": risk_threshold, # risk for ETH
        },}
             }
               }
        """
        user_positions[user_id][asset] = { # here we are saving the user data like assets , position size and risk threshold
            "entry_price": current_price,
            "position_size": position_size,
            "risk_threshold": risk_threshold,
        }
        await update.message.reply_text( # reply to user to maintain the user interaction
            f"✅ Monitoring started for {asset}\n"
            f"Current Price: ${current_price:.2f}\n"
            f"Risk Threshold: {risk_threshold}%"
        )
        """
        it give the user an idea how the bot going to take an output 
        """
    except Exception as e:
        await update.message.reply_text(
            " Usage: /monitor_risk <asset> <position_size> <risk_threshold>"
        )

# --- Example inline action (Hedge Now) ---
async def hedge_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /hedge_now <asset> <size>")
        return

    asset = context.args[0].upper()
    if not asset.endswith("USDT"):
        asset += "USDT"

    try:
        size = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid size format. Use a number.")
        return

    # Check user position
    if user_id not in user_positions or asset not in user_positions[user_id]:
        await update.message.reply_text(
            f"❌ No data found for {asset}.\nAvailable assets: {', '.join(user_positions.get(user_id, {}).keys())}"
        )
        return

    try:
        # Get product ID
        get_product_id = product_id(asset)  # This must return a valid product ID string
        if not get_product_id:
            await update.message.reply_text("❌ Invalid product ID.")
            return

        # Get current price
        current_price = get_spot_price(asset)  # Must return float

        # Place the order
        response = place_hedge_order(get_product_id, size, current_price)

        # Save hedge log
        hedge_log = {
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "order_id": response.get("id", "N/A"),
            "side": "SELL",
            "size": size,
            "status": response.get("status", "UNKNOWN"),
        }
        user_positions[user_id][asset].setdefault("hedge_logs", []).append(hedge_log)

        # Notify user
        await update.message.reply_text(
            f"✅ Hedge placed for {asset}:\n"
            f"🔹 Order ID: {hedge_log['order_id']}\n"
            f"🔹 Side: {hedge_log['side']} {hedge_log['size']}\n"
            f"🔹 Price: ${current_price:.2f}\n"
            f"🔹 Status: {hedge_log['status']}\n"
            f"🕒 {hedge_log['time']}"
        )

    except Exception as e:
        print("Manual hedge error:", e)
        await update.message.reply_text("❌ Failed to place hedge order.")

async def auto_hedge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_positions or not user_positions[user_id]:
        await update.message.reply_text("⚠️ You haven't started monitoring any assets yet.")
        return
    try:
        if context.args:
            asset = context.args[0].upper()
            if asset in user_positions[user_id]:
                user_positions[user_id][asset]["auto_hedge"]=True
                await update.message.reply_text(f"you have started Auto-hedging for {asset}")
            else:
                await update.message.reply_text("you don't have this asset yet add it in monitor")
        else:
            for asset in user_positions[user_id]:
                user_positions[user_id][asset]["auto_hedge"]=True
                await update.message.reply_text(f"you have started Auto-hedging for all assets in your position")
    except Exception as e:
        await update.message.reply_text("Something went wrong")
# --- Callback from button press ---
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == "confirm_hedge":
        query.edit_message_text("🛡 Hedging position now... (this would trigger hedge logic)")
        # TODO: trigger real hedge logic
    elif query.data == "cancel_hedge":
        query.edit_message_text(" Hedge cancelled.")
def product_id(symbol_name, update: Update):
    user_id = update.effective_user.id
    url = "https://api.delta.exchange/v2/products"
    response = requests.get(url)
    data = response.json()
    user_positions[user_id][symbol_name]["product_id"] = data["result"]["id"]
    for product in data["result"]:
        if product["symbol"] == symbol_name:
            return product["id"]
    return None
async def update_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_positions or not user_positions[user_id]:
        await update.message.reply_text("❌ You don't have any active positions.")
        return

    try:
        if context.args:
            asset = context.args[0].upper()
            new_threshold = float(context.args[1])

            if asset not in user_positions[user_id]:
                await update.message.reply_text(f"❌ {asset} is not in your positions.")
                return

            # Initialize history list if not present
            if "risk_threshold_history" not in user_positions[user_id][asset]:
                user_positions[user_id][asset]["risk_threshold_history"] = []

            user_positions[user_id][asset]["risk_threshold_history"].append({
                "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "old_threshold": user_positions[user_id][asset]["risk_threshold"],
                "new_threshold": new_threshold,
            })

            user_positions[user_id][asset]["risk_threshold"] = new_threshold
            await update.message.reply_text(f"✅ Threshold for {asset} updated to {new_threshold:.2f}%.")
        else:
            await update.message.reply_text("⚠️ Usage: `/update_threshold <asset> <new_threshold>`", parse_mode="Markdown")
    except Exception as e:
        print("Threshold update error:", e)
        await update.message.reply_text("❌ Something went wrong while updating the threshold.")

async def full_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_positions:
        await update.message.reply_text("No assets being tracked.")
        return

    for asset, data in user_positions[user_id].items():
        msg = f"📘 *Analytics for {asset}*:\n"
        msg += f"🪙 Entry Price: ${data['entry_price']:.2f}\n"
        msg += f"⚠️ Threshold: {data['risk_threshold']}%\n"
        msg += f"🤖 Auto-Hedge: {'ON' if data.get('auto_hedge') else 'OFF'}\n"

        msg += "\n📉 *Price History (Last 5)*:\n"
        for p in data.get("price_history", [])[-5:]:
            msg += f" - {p['time']} ➜ ${p['price']:.2f}\n"

        msg += "\n🔄 *Threshold Changes:*\n"
        for t in data.get("risk_threshold_history", []):
            msg += f" - {t['time']}: {t['old_threshold']}% ➜ {t['new_threshold']}%\n"

        msg += "\n🛡️ *Hedge Logs:*\n"
        for h in data.get("hedge_logs", []):
            msg += f" - {h['time']} | Order: {h['order_id']} | {h['side']} {h['size']} | {h['status']}\n"

        await update.message.reply_text(msg, parse_mode='Markdown')






