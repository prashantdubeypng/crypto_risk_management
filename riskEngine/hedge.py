import json
import os

import requests
import time
import hashlib
import hmac
import dotenv as dotenv
dotenv.load_dotenv()
API_KEY = os.getenv("DELTA_API_KEY")
API_SECRET = os.getenv("DELTA_API_SECRET")
BASE_URL = os.getenv("DELTA_BASE_URL")

def create_signature(api_secret, req_time, method, endpoint, payload=''):
    message = f"{req_time}{method.upper()}{endpoint}{payload}"
    return hmac.new(api_secret.encode(), message.encode(), hashlib.sha256).hexdigest()

def place_hedge_order(product_id, size, price, order_type="limit"):
    endpoint = "/v2/orders"
    url = BASE_URL + endpoint
    method = "POST"
    req_time = str(int(time.time() * 1000))

    body = {
        "product_id": product_id,
        "limit_price": str(price),
        "size": str(size),
        "side": "sell",  # Hedge is typically a short
        "order_type": order_type,
        "time_in_force": "gtc"
    }
    payload = json.dumps(body)
    signature = create_signature(API_SECRET, req_time, method, endpoint, payload)

    headers = {
        "api-key": API_KEY,
        "timestamp": req_time,
        "signature": signature,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=payload)
    return response.json()
