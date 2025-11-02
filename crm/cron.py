from datetime import datetime
import requests

def log_crm_heartbeat():
    timestamp = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    try:
        r = requests.post("http://localhost:8000/graphql", json={"query": "{ hello }"})
        if r.status_code == 200:
            status = "CRM is alive and responsive"
        else:
            status = f"CRM is alive but returned {r.status_code}"
    except Exception as e:
        status = f"CRM heartbeat failed: {e}"

    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(f"{timestamp} - {status}\n")


def update_low_stock():
    from datetime import datetime
    import requests

    query = """
    mutation {
      updateLowStockProducts {
        success
        updatedProducts
      }
    }
    """
    response = requests.post("http://localhost:8000/graphql", json={"query": query})
    data = response.json()

    with open("/tmp/low_stock_updates_log.txt", "a") as log:
        log.write(f"\n{datetime.now()} - Stock update run:\n")
        for item in data.get("data", {}).get("updateLowStockProducts", {}).get("updatedProducts", []):
            log.write(f"{item}\n")
