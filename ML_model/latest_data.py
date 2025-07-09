import requests # Import the requests library for making HTTP requests to external APIs
import pandas as pd # Import the pandas library, although not strictly used in this specific file, it's a common dependency for data handling

def fetch_latest_ohlcv_from_binance():
    """
    Fetches the latest 1-hour OHLCV (Open, High, Low, Close, Volume) data for BTC/USDT from Binance.
    This function interacts with the Binance public API.
    """
    url = 'https://api.binance.com/api/v3/klines' # Binance API endpoint for candlestick data
    params = {
        'symbol': 'BTCUSDT',  # Specify the trading pair (Bitcoin / Tether)
        'interval': '1h',     # Specify the candlestick interval (1 hour)
        'limit': 1            # Request only the most recent complete candlestick
    }

    try:
        # Send a GET request to the Binance API with the specified parameters
        res = requests.get(url, params=params)
        # Raise an HTTPError for bad responses (4xx or 5xx)
        res.raise_for_status()
        # Parse the JSON response from the API
        data = res.json()

        # Binance API returns a list of klines, each kline is a list of values.
        # We only requested 1 kline (limit=1), so we access the first element [0].
        # The indices for OHLCV are:
        # kline[1]: Open price
        # kline[2]: High price
        # kline[3]: Low price
        # kline[4]: Close price (not used here, but often part of OHLCV)
        # kline[5]: Volume
        kline = data[0]
        ohlcv = {
            'open': float(kline[1]),   # Convert open price to float
            'high': float(kline[2]),   # Convert high price to float
            'low': float(kline[3]),    # Convert low price to float
            'volume': float(kline[5])  # Convert volume to float
        }
        return ohlcv # Return the extracted OHLCV data as a dictionary

    except Exception as e:
        # Catch any exceptions that occur during the API request or data processing
        print(f"Binance fetch failed: {e}") # Print an informative error message
        # Return default zero values in case of an error to prevent application crashes.
        # This allows the ML prediction to proceed with a fallback, albeit less accurate, input.
        return {
            'open': 0.0,
            'high': 0.0,
            'low': 0.0,
            'volume': 0.0
        }


def get_latest_btc_input():
    """
    Returns the latest BTC input data for prediction.
    This function acts as an adapter, fetching data and preparing it
    in a format expected by the ML model (e.g., specific dictionary keys).
    """
    # Call the helper function to fetch the OHLCV data
    data = fetch_latest_ohlcv_from_binance()
    # Return the fetched data. The keys 'open', 'high', 'low', 'volume'
    # match the feature names used during the ML model's training.
    return data