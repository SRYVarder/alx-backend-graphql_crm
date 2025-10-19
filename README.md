# alx-backend-graphql_crm
Minimal Django + Graphene project for the "Understanding GraphQL" assignment.

## Setup
1. Create a venv and install requirements:
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt
2. Run migrations and seed:
   python manage.py migrate
   python seed_db.py
3. Run server:
   python manage.py runserver
4. Visit GraphiQL at http://127.0.0.1:8000/graphql

## Notes
- The schema exposes `hello` query and Relay-style connection fields `allCustomers`, `allProducts`, `allOrders` with django-filter support.
- Mutations implemented: createCustomer, bulkCreateCustomers, createProduct, createOrder.
- Filters: see crm/filters.py
