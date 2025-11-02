#!/bin/bash
# clean_inactive_customers.sh
# Deletes customers with no orders in the past year

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting cleanup..." >> /tmp/customer_cleanup_log.txt

python3 manage.py shell <<EOF
from crm.models import Customer, Order
from datetime import datetime, timedelta
cutoff = datetime.now() - timedelta(days=365)
inactive_customers = Customer.objects.exclude(order__order_date__gte=cutoff)
count = inactive_customers.count()
inactive_customers.delete()
print(f"{count} inactive customers deleted.")
EOF

echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup complete" >> /tmp/customer_cleanup_log.txt
