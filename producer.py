import time
from datetime import datetime

import requests

BROKER_URL = "http://127.0.0.1:6000/queue/orders"

order_id = 1

while True:
    message = {
        "order_id": order_id,
        "created_at": str(datetime.now())
    }

    response = requests.post(BROKER_URL, json=message)

    print(
        f"Sent order {order_id} | "
        f"status: {response.status_code} | "
        f"time: {message['created_at']}"
    )

    order_id += 1
    time.sleep(1)