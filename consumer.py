import time

import requests

BROKER_URL = "http://127.0.0.1:6000/queue/orders"

while True:
    response = requests.get(BROKER_URL)

    if response.status_code == 200:
        message = response.json()

        print(f"Received: {message}")
        print("Processing...")

        time.sleep(3)

        print(f"Processed order {message['order_id']}")
        print()

    elif response.status_code == 204:
        print("Queue is empty. Waiting...")
        time.sleep(2)

    else:
        print(f"Error: {response.status_code}")
        time.sleep(2)