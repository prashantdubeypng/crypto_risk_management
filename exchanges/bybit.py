import requests  # Import the requests library for making HTTP requests.

BASE_URL = "https://api.bybit.com/v5/market/tickers"  # Define the base URL for the Bybit market tickers API endpoint.


def get_spot_price(symbol1: str) -> float:
    """
    Fetch the current spot price of a given asset from the Bybit API.

    Args:
        symbol1 (str): The base asset symbol (e.g., "BTC", "ETH").
                       This will be appended with "USDT" to form the full trading pair.

    Returns:
        float: The current spot price of the asset in USDT if successful,
               otherwise None in case of an error.
    """
    # Construct the full trading symbol by converting the input symbol to uppercase
    # and appending "USDT" (e.g., "BTC" -> "BTCUSDT").
    symbol = symbol1.upper() + "USDT"

    try:
        # Make a GET request to the Bybit API.
        # 'category': "spot" specifies we want spot market data.
        # 'symbol': the constructed trading pair (e.g., "BTCUSDT").
        response = requests.get(BASE_URL, params={"category": "spot", "symbol": symbol})

        # Raise an HTTPError for bad responses (4xx or 5xx status codes).
        response.raise_for_status()

        # Parse the JSON response from the API.
        data = response.json()

        # Check the 'retCode' field in the Bybit API response.
        # A 'retCode' of 0 typically indicates success.
        if data["retCode"] != 0:
            # If 'retCode' is not 0, an API-specific error occurred.
            # Raise an exception with the Bybit's error message.
            raise Exception(f"Bybit API error: {data['retMsg']}")

        # Access the first item in the 'list' within the 'result' field,
        # which contains the ticker data for the requested symbol.
        ticker_data = data["result"]["list"][0]

        # Extract the 'lastPrice' from the ticker data and convert it to a float.
        price = float(ticker_data["lastPrice"])

        # Print a success message to the console with the fetched price.
        print(f"[Bybit API] Fetched spot price for {symbol}: {price}")
        return price  # Return the fetched price.

    except requests.exceptions.HTTPError as http_err:
        # Handle HTTP-specific errors (e.g., 404 Not Found, 500 Internal Server Error).
        print(f"[Bybit API] HTTP error fetching price for {symbol}: {http_err}")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        # Handle network-related errors (e.g., no internet connection, DNS failure).
        print(f"[Bybit API] Connection error fetching price for {symbol}: {conn_err}")
        return None
    except requests.exceptions.Timeout as timeout_err:
        # Handle request timeout errors.
        print(f"[Bybit API] Timeout error fetching price for {symbol}: {timeout_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        # Handle any other general requests-related errors.
        print(f"[Bybit API] An error occurred with the request for {symbol}: {req_err}")
        return None
    except IndexError:
        # Handle case where 'list' might be empty or 'result' structure is unexpected.
        print(f"[Bybit API] No ticker data found for {symbol}. Check symbol or API response structure.")
        return None
    except (TypeError, ValueError) as data_err:
        # Handle errors during data parsing (e.g., 'lastPrice' not a valid number).
        print(f"[Bybit API] Data parsing error for {symbol}: {data_err}. Response might be malformed.")
        return None
    except Exception as e:
        # Catch any other unexpected errors.
        print(f"[Bybit API] An unexpected error occurred fetching price for {symbol}: {e}")
        return None