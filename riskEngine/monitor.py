# riskEngine/risk_monitor.py
from cgitb import handler
from riskEngine.hedge import place_hedge_order
from telegram import Bot
from exchanges.bybit import get_spot_price
from datetime import datetime
# This dictionary should be imported/shared with your handlers (or moved to a shared state module)
from TeligramBot.handlers import user_positions,product_id

# Check risk for all users and send alert if risk threshold is breached
async def check_user_risks(bot: Bot):
    for user_id, assets in user_positions.items():
        for asset, data in assets.items():
            current_price = get_spot_price(asset)

            if current_price is None:
                print(f"❌ Could not fetch price for {asset}")
                continue
            data.setdefault("price_history", []).append({
                "time": datetime.utcnow().isoformat(),
                "price": current_price,
            })

            entry_price = data["entry_price"]
            threshold = float(data["risk_threshold"])
            drop_percent = ((entry_price - current_price) / entry_price) * 100

            if drop_percent >= threshold:
                if  data.get("auto_hedge", False):
                    user_positions[user_id][asset]["auto_hedge_history"].append({
                        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                        "istrick":True,
                    })
                    get_product = product_id(asset)
                    if get_product:
                        result = place_hedge_order(get_product, data["size"], current_price)
                        if result:
                            data["hedge_logs"].append({
                                "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                "order_id": result["order_id"],
                                "side": result["side"],
                                "size": result["size"],
                                "status": result["status"]
                            })
                            await bot.send_message(
                                chat_id=user_id,
                                text=(
                                    f"✅ Auto-Hedge Executed!\n\n"
                                    f"📉 Asset: {result['product_symbol']}\n"
                                    f"🛒 Side: {result['side'].upper()}\n"
                                    f"📊 Size: {result['filled_size']}\n"
                                    f"🧾 Order Type: {result['order_type'].capitalize()}\n"
                                    f"📌 Status: {result['state'].capitalize()}\n"
                                    f"📅 Time: {result['created_at'][:16].replace('T', ' ')} UTC\n"
                                    f"📎 Order ID: {result['id']}"
                                )
                            )
                        else:
                            await bot.send_message(chat_id=user_id,text=f"Something went wrong in auto heading\n\n")
                            print("<UNK> <UNK> <UNK> <UNK> <UNK> <UNK> <UNK>")
                message = (
                    f"⚠️ Risk Alert for {asset}!\n"
                    f" Entry Price: ${entry_price:.2f}\n"
                    f" Current Price: ${current_price:.2f}\n"
                    f" Loss: {drop_percent:.2f}% exceeds your threshold of {threshold}%.\n\n"
                    f" Consider hedging your position."
                )
                await bot.send_message(chat_id=user_id, text=message)
            else:
                message = (
                    f"<UNK> NO Risk Alert for {asset}!\n"
                )
                await bot.send_message(chat_id=user_id, text=message)