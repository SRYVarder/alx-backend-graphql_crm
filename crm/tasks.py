from celery import shared_task
from datetime import datetime
import requests

@shared_task
def generate_crm_report():
    endpoint = "http://localhost:8000/graphql"
    query = """
    query {
      totalCustomers
      totalOrders
      totalRevenue
    }
    """

    try:
        response = requests.post(endpoint, json={"query": query})
        data = response.json().get("data", {})
        customers = data.get("totalCustomers", 0)
        orders = data.get("totalOrders", 0)
        revenue = data.get("totalRevenue", 0.0)

        log_line = (
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
            f"Report: {customers} customers, {orders} orders, {revenue} revenue\n"
        )

        with open("/tmp/crm_report_log.txt", "a") as f:
            f.write(log_line)
    except Exception as e:
        with open("/tmp/crm_report_log.txt", "a") as f:
            f.write(f"{datetime.now()} - Error generating report: {e}\n")
