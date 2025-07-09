from riskEngine.hedge import place_hedge_order
from telegram import Bot
from exchanges.bybit import get_spot_price
from datetime import datetime # Datetime module to get the date and time on which we get price of crypto
from TeligramBot.handlers import user_positions, product_id
import numpy as np

"""
IT IS USED TO CHECK THE  RISK MATRIX AND PRICE OF THE ASSET AT FIXED INTERVAL OF TIME AND AT EACH TIME
IT CHECK THE DROP PERCENTAGE AND IF THE DROP PERCENTAGE GET HIGHER THEN THE THRESHOLD
WHICH USER SETS , IF THE USER HAVE SELECTED AUTO HEDGE FEATURE FOR THAT ASSET , USER
GET ALERT AND AUTO_HEDGE GET START , IF NOT THEN THE USER GET AN ALERT ONLY
"""
async def check_user_risks(bot: Bot): # IT HAVE PARAMETERS TO RESPONSE THE USER
    # Iterate through each user in the user_positions dictionary.
    for user_id, assets in user_positions.items():
        # For each user, iterate through their  assets.
        for asset, data in assets.items():
            # Get the current spot price of the asset.
            current_price = get_spot_price(asset)

            # If the price cannot be fetched, print an error and skip to the next asset.
            if current_price is None:
                print(f"Could not fetch price for {asset}")
                continue

            # Save current price to history for risk calculations.
            # Use setdefault to initialize 'price_history' if it doesn't exist.
            data.setdefault("price_history", []).append({
                "time": datetime.utcnow().isoformat(), # Store time in ISO format for consistency.
                "price": current_price,
            })

            # Retrieve risk-related inputs from the asset's data.
            entry_price = data["entry_price"] # PRICE AT WHICH USER GIVE US TO MONITOR
            threshold = float(data["risk_threshold"]) # MAX LOSS USER CAN TAKE
            position_size = data["position_size"] # SIZE OF  ASSET HE HAS

            # Validate the risk threshold: it must be greater than 0.
            if threshold <= 0: # IF IT GOES LESS THAN 0 OR EQUAL TO 0 IT GET ALWAYS TRUE SO ELSE CONDITION NOT GET ON
                await bot.send_message(
                    chat_id=user_id,
                    text=f"⚠️ Invalid risk threshold for {asset}: {threshold}%. Please set it above 0."
                )
                continue

            # Calculate the percentage drop from the entry price to the current price.
            drop_percent = ((entry_price - current_price) / entry_price) * 100
            print(f"[DEBUG] Entry: {entry_price}, Current: {current_price}, Threshold: {threshold}, Drop%: {drop_percent}")

            # === Risk Metrics Calculation ===

            prices = [p["price"] for p in data["price_history"]][-30:]

            # Calculate Spot Delta and Notional Exposure.
            delta = position_size * 1.0  # For spot positions, delta is typically 1.
            notional = position_size * current_price # Total value of the position.

            # Calculate Max Drawdown if there are at least two prices in history.
            if len(prices) >= 2:
                running_max = np.maximum.accumulate(prices) # Calculate cumulative maximums.
                drawdowns = (np.array(prices) - running_max) / running_max # Calculate percentage drawdowns.
                max_drawdown = np.min(drawdowns) * 100 # Find the maximum (most negative) drawdown.
            else:
                max_drawdown = None # Not enough data to calculate.

            # Calculate 1-Day 95% VaR if there are at least 30 prices (for statistical significance).
            if len(prices) >= 30:
                returns = np.diff(np.log(prices)) # Calculate logarithmic returns.
                std_dev = np.std(returns) # Calculate standard deviation of returns.
                z_score = 1.65  # Z-score for 95% confidence level (one-tailed for losses).
                var_1d_95 = notional * std_dev * z_score # Calculate VaR.
            else:
                var_1d_95 = None # Not enough data to calculate.

            # === Risk Trigger ===
            # Check if the drop percentage has exceeded the user's defined threshold.
            if drop_percent >= threshold:
                # If auto-hedge is enabled for this asset.
                if user_positions[user_id][asset].get("auto_hedge") is True:
                    # Log the auto-hedge trigger event.
                    user_positions[user_id][asset].setdefault("auto_hedge_history", []).append({
                        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), # Store UTC time.
                        "istrick": True, # Indicate that the auto-hedge was triggered.
                    })

                    # Get the product ID required for placing a hedge order.
                    get_product = product_id(asset)
                    if get_product:
                        # Place the hedge order using the external risk engine.
                        result = place_hedge_order(get_product, data["size"], current_price)

                        # Handle the result of the hedge order placement.
                        if result.get("error"):
                            print("Hedge failed:", result)
                            await bot.send_message(chat_id=user_id, text=f"Auto-hedge failed:\n{result.get('details')}")
                        elif result:
                            # Log successful hedge order details.
                            data.setdefault("hedge_logs", []).append({
                                "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                "order_id": result["order_id"],
                                "side": result["side"],
                                "size": result["size"],
                                "status": result["status"]
                            })

                            # Send a detailed success message to the user.
                            await bot.send_message(
                                chat_id=user_id,
                                text=(
                                    f" Auto-Hedge Executed!\n\n"
                                    f" Asset: {result['product_symbol']}\n"
                                    f" Side: {result['side'].upper()}\n"
                                    f" Size: {result['filled_size']}\n"
                                    f" Order Type: {result['order_type'].capitalize()}\n"
                                    f" Status: {result['state'].capitalize()}\n"
                                    f" Time: {result['created_at'][:16].replace('T', ' ')} UTC\n"
                                    f" Order ID: {result['id']}"
                                )
                            )
                        else:
                            # Handle unexpected outcomes from place_hedge_order.
                            await bot.send_message(chat_id=user_id, text="Something went wrong in auto-hedging.\n")
                            print(" Unknown error in auto-hedge")
                else:
                    # If auto-hedge is not enabled, send a risk alert message to the user.
                    print("auto_hedge is false")
                    print(user_positions[user_id][asset])

                    risk_msg = (
                        f"⚠ Risk Alert for {asset}!\n"
                        f" Entry Price: ${entry_price:.2f}\n"
                        f" Current Price: ${current_price:.2f}\n"
                        f" Loss: {drop_percent:.2f}% exceeds your threshold of {threshold}%.\n\n"
                        f" Risk Metrics:\n"
                        f" Spot Delta: {delta:.4f} {asset}\n"
                        f" Notional Exposure: ${notional:,.2f}\n"
                    )

                    # Add Max Drawdown and VaR to the message if they were calculated.
                    if max_drawdown is not None:
                        risk_msg += f" Max Drawdown: {max_drawdown:.2f}%\n"
                    if var_1d_95 is not None:
                        risk_msg += f" 1-Day 95% VaR: ${var_1d_95:,.2f}\n"

                    await bot.send_message(chat_id=user_id, text=risk_msg) # Send the alert.

            else:
                # If the drop percentage is below the threshold, no risk alert is triggered.
                print(f"No risk detected for {asset}, sending safe message")
                await bot.send_message(
                    chat_id=user_id,
                    text=f" No Risk Alert for {asset}.\nCurrent Drop: {drop_percent:.2f}% < Threshold: {threshold}%"
                )