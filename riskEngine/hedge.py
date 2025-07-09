import json # Import the json library for working with JSON data.
import os # Import the os library to interact with the operating system (e.g., environment variables).

import requests # Import the requests library for making HTTP requests.
import time # Import the time module for getting the current timestamp.
import hashlib # Import hashlib for hashing algorithms (used in HMAC).
import hmac # Import hmac for HMAC (Hash-based Message Authentication Code) generation.
import dotenv as dotenv # Import dotenv to load environment variables from a .env file.

dotenv.load_dotenv() # Load environment variables from the .env file.
API_KEY = os.getenv("DELTA_API_KEY") # Retrieve the API Key from environment variables.
API_SECRET = os.getenv("DELTA_API_SECRET") # Retrieve the API Secret from environment variables.
BASE_URL = os.getenv("APP_BASE_URL") # Retrieve the base URL for the API from environment variables.

def create_signature(api_secret: str, req_time: str, method: str, endpoint: str, payload: str = '') -> str:
    """
    Generates an HMAC-SHA256 signature for API request authentication.

    The signature is created by hashing a concatenated string of timestamp,
    HTTP method, endpoint, and payload with the API secret key.

    Args:
        api_secret (str): The secret API key provided by the exchange.
        req_time (str): The request timestamp in milliseconds since epoch (as a string).
        method (str): The HTTP method of the request (e.g., "POST", "GET").
        endpoint (str): The API endpoint path (e.g., "/v2/orders").
        payload (str, optional): The JSON string representation of the request body.
                                  Defaults to an empty string for GET requests.

    Returns:
        str: The hexadecimal representation of the HMAC-SHA256 signature.
    """
    # Concatenate the elements to form the message string to be signed.
    # The method is converted to uppercase as per many API signature requirements.
    message = f"{req_time}{method.upper()}{endpoint}{payload}"
    # Create an HMAC-SHA256 hash.
    # The secret key and message must be encoded to bytes.
    return hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def place_hedge_order(product_id: int, size: float, price: float, order_type: str = "limit") -> dict:
    """
    Places a hedge order (sell order) on the exchange.

    This function constructs and sends an authenticated POST request to the
    exchange's order placement endpoint.

    Args:
        product_id (int): The unique identifier for the trading product (e.g., BTC-PERP).
        size (float): The quantity of the asset to hedge.
        price (float): The limit price at which to place the hedge order.
        order_type (str, optional): The type of order (e.g., "limit", "market").
                                     Defaults to "limit".

    Returns:
        dict: A dictionary containing the API response data, or an error dictionary.

    Raises:
        ValueError: If product_id is None.
    """
    if product_id is None:
        raise ValueError("❌ Cannot place order: product_id is None")

    endpoint = "/v2/orders" # Define the API endpoint for placing orders.
    url = BASE_URL + endpoint # Construct the full URL for the request.
    method = "POST" # Define the HTTP method for placing an order.
    req_time = str(int(time.time() * 1000)) # Get current timestamp in milliseconds as a string.

    # Construct the request body as a dictionary.
    body = {
        "product_id": product_id,
        "limit_price": str(price), # Convert price to string as required by some APIs.
        "size": str(size), # Convert size to string.
        "side": "sell",  # A hedge typically involves selling to offset a long spot position.
        "order_type": order_type,
        "time_in_force": "gtc" # Good-Till-Cancelled, a common time-in-force option.
    }

    payload = json.dumps(body) # Convert the request body dictionary to a JSON string.
    # Generate the signature for the request.
    signature = create_signature(API_SECRET, req_time, method, endpoint, payload)

    # Define the HTTP headers required for authentication and content type.
    headers = {
        "api-key": API_KEY,
        "timestamp": req_time,
        "signature": signature,
        "Content-Type": "application/json"
    }

    # Send the POST request to the API.
    response = requests.post(url, headers=headers, data=payload)

    try:
        response_data = response.json() # Attempt to parse the JSON response.
    except requests.exceptions.JSONDecodeError as e:
        # Handle cases where the response is not valid JSON.
        print("❌ Failed to parse response JSON:", e)
        return {"error": "Invalid JSON response", "details": response.text}
    except Exception as e:
        # Catch any other unexpected errors during JSON parsing.
        print("❌ An unexpected error occurred while parsing JSON:", e)
        return {"error": "Unexpected JSON parsing error", "details": response.text}


    # Check the HTTP status code of the response.
    if response.status_code != 200:
        # If the status code is not 200 (OK), print an error and return details.
        print("❌ API Error:", response.status_code, response_data)
        return {"error": "Order rejected", "status": response.status_code, "details": response_data}

    # Log success message if the order was placed successfully.
    print("✅ Order placed successfully:", response_data)
    return response_data # Return the full JSON response data.