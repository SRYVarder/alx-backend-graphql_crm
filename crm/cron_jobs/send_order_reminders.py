#!/usr/bin/env python3
import requests
from datetime import datetime, timedelta
from gql import gql, Client

endpoint = "http://localhost:8000/graphql"
query = f"""
query {{
  orders(orderDateGte: "{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}") {{
    id
    customer {{
      email
    }}
  }}
}}
"""

response = requests.post(endpoint, json={"query": query})
data = response.json()

with open("/tmp/order_reminders_log.txt", "a") as log:
    log.write(f"\n{datetime.now()} - Order reminders processed:\n")
    for order in data.get("data", {}).get("orders", []):
        log.write(f"Order ID: {order['id']}, Customer: {order['customer']['email']}\n")

print("Order reminders processed!")
