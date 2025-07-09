"""
Module: Telegram Bot Handlers

This module contains asynchronous functions that act as handlers for various
commands and callback queries received by the Telegram bot. It manages user
interactions related to cryptocurrency risk monitoring, auto-hedging, manual
hedging, and provides analytics.

Key Features:
- User onboarding and command listing (`/start`).
- Monitoring of cryptocurrency assets with user-defined risk thresholds (`/monitor_risk`).
- Toggling automated hedging based on risk breaches (`/auto_hedge`, `/disable_auto_hedge`).
- Manual placement of hedge orders (`/hedge_now`).
- Stopping asset monitoring (`/stop_monitor_risk`).
- Updating risk thresholds for existing positions (`/update_threshold`).
- Providing comprehensive analytics and history for monitored assets (`/View_full_analytics`).

Data Storage:
- `user_positions`: A global dictionary used to store all user-specific data
  related to their monitored assets, including entry prices, position sizes,
  risk thresholds, price history, auto-hedge status, and hedge logs.
"""

# IMPORTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ContextTypes
import requests
from datetime import datetime

from ML_model.predict import predict_btc
from exchanges.bybit import get_spot_price
from riskEngine.hedge import place_hedge_order

# Global dictionary to store user-specific asset monitoring data.
# Structure: {user_id: {asset_symbol: { "entry_price": float, "position_size": float, "risk_threshold": float, "price_history": [], "auto_hedge": bool, "hedge_logs": [], "risk_threshold_history": [] }}}
user_positions = {}

# --- Start command ---
async def start(update: Update, context: CallbackContext):
    """
    Handles the /start command. Greets the user and provides a list of available commands.

    Args:
        update (Update): The incoming Telegram update.
        context (CallbackContext): The context object for the current update.
    """
    user = update.effective_user # Get information about the user who sent the command.
    message = ( # Define the welcome message with available commands.
        f" Hello {user.first_name}!\n\n"
        "I'm your Crypto Risk Hedging Bot. Use the menu or commands below to get started:\n\n"
        " /monitor_risk <asset> <position_size> <risk_threshold>\n"
        " /predict_Bitcoin_price\n"
        "️ /auto_hedge <asset> @your hedge automatically started when threshold get trick of the monitor_risk \n"
        " /update_threshold <asset> <new threshold>\n"
        " /View_full_analytics <to get whole report about all assets\n"
        " /stop_monitor_risk <asset>\n"
        " /hedge_now <asset> <size>\n"
        " /disable_auto_hedge <asset>\n"
        " /hedge_history <asset> <timeframe>\n"
    )
    await update.message.reply_text(message) # Send the predefined message back to the user.

async def disable_auto_hedge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Disables the auto-hedge feature for a specified asset or all assets for a user.

    Args:
        update (Update): The incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context object containing command arguments.
    """
    user_id = update.effective_user.id # Get the user's ID.
    # Check if the user has any positions being monitored.
    if user_id not in user_positions:
        await update.message.reply_text("You have not yet started monitoring any assets.")
        return

    try:
        if context.args:
            # If an asset is specified, disable auto-hedge for that specific asset.
            asset = context.args[0].upper() # Get asset name and convert to uppercase.
            if asset in user_positions[user_id]:
                user_positions[user_id][asset]["auto_hedge"] = False # Set auto_hedge flag to False.
                await update.message.reply_text(f"Auto hedge disabled for {asset}.")
            else:
                await update.message.reply_text(f"{asset} not in your holdings. Please add it via /monitor_risk.")
        else:
            # If no asset is specified, disable auto-hedge for all monitored assets for the user.
            for asset_name in user_positions[user_id]:
                user_positions[user_id][asset_name]["auto_hedge"] = False
            await update.message.reply_text("Auto hedge disabled for all your monitored assets.")
    except Exception as e:
        # Catch any unexpected errors during the process.
        await update.message.reply_text(f"Something went wrong while disabling auto-hedge: {e}")

async def Stop_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Stops monitoring for a specified asset or all assets for a user.
    Args:
        update (Update): The incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context object containing command arguments.
    """
    user_id = update.effective_user.id # Get the user's ID.
    # Check if the user is monitoring any assets.
    if user_id not in user_positions:
        await update.message.reply_text("You are not monitoring any assets.")
        return

    try:
        if context.args:
            # If an asset is specified, stop monitoring for that specific asset.
            asset = context.args[0].upper() # Get asset name and convert to uppercase.
            if asset in user_positions[user_id]:
                del user_positions[user_id][asset] # Remove the asset from the user's monitored positions.
                # If the user has no more assets being monitored, remove their entry from user_positions.
                if not user_positions[user_id]:
                    del user_positions[user_id]
                await update.message.reply_text(f"Stopped monitoring for {asset}.")
            else:
                await update.message.reply_text(" You are not monitoring this asset.")
        else:
            # If no asset is specified, stop monitoring for all assets for the user.
            del user_positions[user_id] # Remove all entries for the user ID.
            await update.message.reply_text(" Stopped monitoring for all assets.")
    except Exception as e:
        # Catch any unexpected errors.
        await update.message.reply_text(f" Failed to stop monitoring. Usage: /stop_monitor_risk <asset> (Error: {e})")

# --- Monitor command ---
async def monitor_risk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /monitor_risk command. Allows a user to start monitoring a
    cryptocurrency asset with a specified position size and risk threshold.

    Usage: /monitor_risk <asset> <position_size> <risk_threshold>
    Example: /monitor_risk BTC 5 20 (Monitors BTC, position size 5, 20% risk threshold)

    Args:
        update (Update): The incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context object containing command arguments.
    """
    try:
        user_id = update.effective_user.id # Get the unique ID of the user.
        asset = context.args[0].upper() # Get the asset symbol (e.g., "BTC") and convert to uppercase.
        position_size = float(context.args[1]) # Get the user's position size (e.g., 5 BTC).
        risk_threshold = float(context.args[2]) # Get the user's acceptable risk threshold in percentage (e.g., 20%).

        # Fetch the current spot price of the asset.
        current_price = get_spot_price(asset)
        if current_price is None:
            await update.message.reply_text("Failed to fetch current price for the asset. Please try again later.")
            return

        # Initialize the user's entry in user_positions if it doesn't exist.
        if user_id not in user_positions:
            user_positions[user_id] = {}

        # Store the asset's monitoring data in the nested dictionary.
        # This structure allows tracking multiple assets per user:
        # user_positions = {
        #   user_id_1: {
        #     "BTC": { "entry_price": X, "position_size": Y, "risk_threshold": Z, "auto_hedge": False, ... },
        #     "ETH": { "entry_price": A, "position_size": B, "risk_threshold": C, "auto_hedge": False, ... }
        #   },
        #   user_id_2: { ... }
        # }
        user_positions[user_id][asset] = {
            "entry_price": current_price, # The price at which monitoring started.
            "position_size": position_size,
            "risk_threshold": risk_threshold,
            "auto_hedge": False, # Auto-hedge is off by default.
            "price_history": [{"time": datetime.utcnow().isoformat(), "price": current_price}], # Initialize price history.
            "hedge_logs": [], # Initialize an empty list for hedge logs.
            "risk_threshold_history": [], # Initialize an empty list for threshold change logs.
        }

        # Send a confirmation message to the user.
        await update.message.reply_text(
            f"Monitoring started for {asset}\n"
            f"Current Price: ${current_price:.2f}\n"
            f"Risk Threshold: {risk_threshold}%"
        )

    except (IndexError, ValueError):
        # Catch errors if the command arguments are missing or malformed.
        await update.message.reply_text(
            " Invalid usage. Please use: `/monitor_risk <asset> <position_size> <risk_threshold>` (e.g., `/monitor_risk BTC 0.5 10`)",
            parse_mode="Markdown"
        )
    except Exception as e:
        # Catch any other unexpected errors.
        await update.message.reply_text(f" An error occurred: {e}. Please try again.")


# --- Example inline action (Hedge Now) ---
async def hedge_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /hedge_now command. Allows a user to manually place a hedge order.

    Usage: /hedge_now <asset> <size>
    Example: /hedge_now BTC 0.1 (Place a hedge order for 0.1 BTC)

    Args:
        update (Update): The incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context object containing command arguments.
    """
    user_id = update.effective_user.id # Get the user's ID.

    # Check if correct number of arguments are provided.
    if len(context.args) < 2:
        await update.message.reply_text(" Usage: `/hedge_now <asset> <size>`", parse_mode="Markdown")
        return

    asset = context.args[0].upper() # Get asset symbol and convert to uppercase.
    # Map common asset symbols to their corresponding perpetual contract symbols on Bybit (example).
    # This mapping might need to be dynamic or fetched from an API in a real system.
    symbol_map = {
        "BTC": "BTCUSDT", # Assuming USDT perpetual for hedging spot BTC
        "ETH": "ETHUSDT", # Assuming USDT perpetual for hedging spot ETH
        "BTC-PERP": "BTCUSDT-PERP", # Example for a direct perpetual symbol
        "ETH-PERP": "ETHUSDT-PERP",
    }

    delta_symbol = symbol_map.get(asset) # Get the corresponding hedging symbol.
    if not delta_symbol:
        await update.message.reply_text(" Unknown asset symbol for hedging. Please use BTC, ETH, etc.")
        return

    try:
        size = float(context.args[1]) # Get the size of the hedge order.
    except ValueError:
        await update.message.reply_text(" Invalid size format. Please enter a numerical value.")
        return

    # Check if the user has this asset in their monitored positions.
    if user_id not in user_positions or asset not in user_positions[user_id]:
        await update.message.reply_text(
            f" No monitoring data found for {asset}. Please use /monitor_risk first."
            f"\nCurrently monitored assets: {', '.join(user_positions.get(user_id, {}).keys())}"
        )
        return

    try:
        # Get the product ID for the hedging symbol from an external source.
        get_product_id = product_id(delta_symbol)
        if not get_product_id:
            await update.message.reply_text(f" Could not find product ID for {delta_symbol}. Cannot place hedge.")
            return

        # Get the current price of the asset for the hedge order.
        current_price = get_spot_price(asset)
        if current_price is None:
            await update.message.reply_text(" Failed to fetch current price. Cannot place hedge.")
            return

        # Place the hedge order via the risk engine.
        response = place_hedge_order(get_product_id, size, current_price)

        # Log the details of the placed hedge order.
        hedge_log = {
            "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "order_id": response.get("id", "N/A"), # Get order ID or "N/A".
            "side": "SELL", # Assuming hedge implies selling to offset long spot position.
            "size": size,
            "status": response.get("state", "UNKNOWN"), # Using 'state' if 'status' isn't available.
        }
        # Add the hedge log to the asset's history.
        user_positions[user_id][asset].setdefault("hedge_logs", []).append(hedge_log)

        # Notify the user about the successful hedge placement.
        await update.message.reply_text(
            f" Hedge placed for {asset}:\n"
            f" Order ID: {hedge_log['order_id']}\n"
            f" Side: {hedge_log['side']} {hedge_log['size']}\n"
            f" Price: ${current_price:.2f}\n"
            f" Status: {hedge_log['status']}\n"
            f" {hedge_log['time']}"
        )

    except Exception as e:
        print(f"Manual hedge error for user {user_id}, asset {asset}: {e}")
        await update.message.reply_text(" Failed to place hedge order. An internal error occurred.")

async def auto_hedge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Enables the auto-hedge feature for a specified asset or all assets for a user.

    Args:
        update (Update): The incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context object containing command arguments.
    """
    user_id = update.effective_user.id # Get the user's ID.
    # Check if the user has any assets being monitored.
    if user_id not in user_positions or not user_positions[user_id]:
        await update.message.reply_text(" You haven't started monitoring any assets yet. Use /monitor_risk.")
        return

    try:
        if context.args:
            # If an asset is specified, enable auto-hedge for that specific asset.
            asset = context.args[0].upper() # Get asset name and convert to uppercase.
            if asset in user_positions[user_id]:
                user_positions[user_id][asset]["auto_hedge"] = True # Set auto_hedge flag to True.
                await update.message.reply_text(f"Auto-hedging enabled for {asset}.")
            else:
                await update.message.reply_text(f"You don't have {asset} in your monitored positions. Please add it via /monitor_risk.")
        else:
            # If no asset is specified, enable auto-hedge for all monitored assets for the user.
            for asset_name in user_positions[user_id]:
                user_positions[user_id][asset_name]["auto_hedge"] = True
            await update.message.reply_text(" Auto-hedging enabled for all assets in your portfolio.")
    except Exception as e:
        # Catch any unexpected errors.
        await update.message.reply_text(f"Something went wrong while enabling auto-hedge: {e}")

# --- Callback from button press ---
def button_callback(update: Update, context: CallbackContext):
    """
    Handles callback queries from inline keyboard buttons. (Currently placeholders).

    Args:
        update (Update): The incoming Telegram update (specifically a callback query).
        context (CallbackContext): The context object for the current update.
    """
    query = update.callback_query # Get the callback query object.
    query.answer() # Acknowledge the callback query to remove the "loading" state from the button.

    # Check the data associated with the pressed button.
    if query.data == "confirm_hedge":
        query.edit_message_text("🛡 Hedging position now... (this would trigger real hedge logic)")
        # TODO: Implement actual hedge logic here when this button is used.
    elif query.data == "cancel_hedge":
        query.edit_message_text(" Hedge cancelled.")

def product_id(symbol_name):
    """
    Fetches the product ID for a given symbol from Delta Exchange API.
    This ID is often required by trading APIs to identify specific trading pairs/products.

    Args:
        symbol_name (str): The trading symbol (e.g., "BTCUSDT", "ETHUSDQ").

    Returns:
        str or None: The product ID if found, otherwise None.
    """
    url = "https://api.delta.exchange/v2/products" # API endpoint for products.
    response = requests.get(url) # Make an HTTP GET request.
    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx).
    data = response.json() # Parse the JSON response.

    # Iterate through the products to find the matching symbol.
    for product in data["result"]:
        if product["symbol"] == symbol_name:
            return product["id"] # Return the product's ID.
    return None # Return None if no matching symbol is found.


async def update_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /update_threshold command. Allows a user to change the risk threshold
    for a specific monitored asset.

    Usage: /update_threshold <asset> <new_threshold>
    Example: /update_threshold BTC 15 (Updates BTC's risk threshold to 15%)

    Args:
        update (Update): The incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context object containing command arguments.
    """
    user_id = update.effective_user.id # Get the user's ID.
    # Check if the user has any active positions being monitored.
    if user_id not in user_positions or not user_positions[user_id]:
        await update.message.reply_text(" You don't have any active positions being monitored. Use /monitor_risk first.")
        return

    try:
        if context.args and len(context.args) == 2:
            asset = context.args[0].upper() # Get asset symbol and convert to uppercase.
            new_threshold = float(context.args[1]) # Get the new risk threshold.

            if asset not in user_positions[user_id]:
                await update.message.reply_text(f" {asset} is not in your monitored positions.")
                return

            # Initialize 'risk_threshold_history' list if it doesn't exist for the asset.
            if "risk_threshold_history" not in user_positions[user_id][asset]:
                user_positions[user_id][asset]["risk_threshold_history"] = []

            # Log the old and new threshold with a timestamp.
            user_positions[user_id][asset]["risk_threshold_history"].append({
                "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "old_threshold": user_positions[user_id][asset]["risk_threshold"],
                "new_threshold": new_threshold,
            })

            user_positions[user_id][asset]["risk_threshold"] = new_threshold # Update the active threshold.
            await update.message.reply_text(f" Threshold for {asset} updated to {new_threshold:.2f}%.")
        else:
            # Provide correct usage if arguments are missing or incorrect.
            await update.message.reply_text("️ Usage: `/update_threshold <asset> <new_threshold>`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text(" Invalid threshold format. Please enter a number for the new threshold.")
    except Exception as e:
        print(f"Threshold update error for user {user_id}, asset {asset}: {e}")
        await update.message.reply_text(" Something went wrong while updating the threshold.")

async def full_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /View_full_analytics command. Provides a detailed report
    on all assets a user is monitoring, including entry price, current threshold,
    auto-hedge status, price history, threshold change history, and hedge logs.

    Args:
        update (Update): The incoming Telegram update.
        context (ContextTypes.DEFAULT_TYPE): The context object.
    """
    user_id = update.effective_user.id # Get the user's ID.
    # Check if the user has any assets being tracked.
    if user_id not in user_positions or not user_positions[user_id]:
        await update.message.reply_text("No assets are currently being tracked for analytics.")
        return

    # Iterate through each asset the user is monitoring.
    for asset, data in user_positions[user_id].items():
        msg = f"*Analytics for {asset}*:\n" # Start building the message for the current asset.
        msg += f" Entry Price: ${data['entry_price']:.2f}\n"
        msg += f"️ Threshold: {data['risk_threshold']}%\n"
        msg += f" Auto-Hedge: {'ON' if data.get('auto_hedge') else 'OFF'}\n" # Display auto-hedge status.

        msg += "\n *Price History (Last 5)*:\n"
        # Display the last 5 price history entries, if available.
        if data.get("price_history"):
            for p in data["price_history"][-5:]:
                msg += f" - {p['time'][:16].replace('T', ' ')} UTC ➜ ${p['price']:.2f}\n" # Format time for display.
        else:
            msg += " - No price history available.\n"


        msg += "\n *Threshold Changes:*\n"
        # Display historical threshold changes.
        if data.get("risk_threshold_history"):
            for t in data["risk_threshold_history"]:
                msg += f" - {t['time']}: {t['old_threshold']:.2f}% ➜ {t['new_threshold']:.2f}%\n"
        else:
            msg += " - No threshold change history.\n"


        msg += "\n *Hedge Logs:*\n"
        # Display hedge order logs.
        if data.get("hedge_logs"):
            for h in data["hedge_logs"]:
                msg += f" - {h['time']} | Order: {h['order_id']} | {h['side']} {h['size']} | {h['status']}\n"
        else:
            msg += " - No hedge logs available.\n"

        # Send the compiled analytics message for the current asset.
        await update.message.reply_text(msg, parse_mode='Markdown')
async def predict_btc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ans = await predict_btc(context.bot, update.effective_chat.id)
    print(ans)