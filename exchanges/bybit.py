
import requests

BASE_URL = "https://api.bybit.com/v5/market/tickers"


def get_spot_price(symbol1: str) -> float:
    symbol = symbol1.upper()+"USDT"
    """
    Fetches the current price of a given asset from the Bybit public API.

    Args:
        symbol (str): The asset symbol (e.g., "BTCUSDT", "ETHUSDT")

    Returns:
        float: The current price of the asset
    """
    try:
        response = requests.get(BASE_URL, params={"category": "spot"})
        response.raise_for_status()

        data = response.json()
        if data["retCode"] != 0:
            raise Exception(f"Bybit API error: {data['retMsg']}")

        for ticker in data["result"]["list"]:
            if ticker["symbol"].upper() == symbol.upper():
                return float(ticker["lastPrice"])

        raise ValueError(f"Symbol {symbol} not found in Bybit spot tickers.")

    except Exception as e:
        print(f"[Bybit API] Error fetching price for {symbol}: {e}")
        return None
