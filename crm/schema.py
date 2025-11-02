import graphene
from .types import CustomerType
from graphene_django import DjangoObjectType
from graphene import relay
from django.db import transaction
from .models import Customer, Product, Order, OrderItem
from .filters import CustomerFilter, ProductFilter, OrderFilter
from graphene_django.filter import DjangoFilterConnectionField
import re, datetime, decimal
from crm.models import Product

class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node, )
        fields = '__all__'
class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node, )
        fields = '__all__'
class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node, )
        fields = '__all__'
# Query: hello and lists with filters
class Query(graphene.ObjectType):
    hello = graphene.String()
    customer = relay.Node.Field(CustomerNode)
    product = relay.Node.Field(ProductNode)
    order = relay.Node.Field(OrderNode)
    all_customers = DjangoFilterConnectionField(CustomerNode, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductNode, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderNode, filterset_class=OrderFilter)
    def resolve_hello(self, info):
        return "Hello, GraphQL!"
# Input types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()
class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Float(required=True)
    stock = graphene.Int()
# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    customer = graphene.Field(lambda: CustomerNode)
    message = graphene.String()
    errors = graphene.List(graphene.String, CustomerType)
    @staticmethod
    def mutate(root, info, input):
        # validate email unique, phone format
        errors = []
        if Customer.objects.filter(email=input.email).exists():
            errors.append('Email already exists')
            return CreateCustomer(customer=None, message='Failed', errors=errors)
        if input.phone:
            if not re.match(r'^(\+\d+|\d{3}-\d{3}-\d{4})$', input.phone):
                errors.append('Invalid phone format')
                return CreateCustomer(customer=None, message='Failed', errors=errors)
        customer = Customer.objects.create(name=input.name, email=input.email, phone=input.phone or '')
        return CreateCustomer(customer=customer, message='Customer created', errors=None)
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)
    customers = graphene.List(lambda: CustomerNode)
    errors = graphene.List(graphene.String)
    @staticmethod
    def mutate(root, info, inputs):
        created = []
        errors = []
        from django.db import IntegrityError
        for i, data in enumerate(inputs):
            try:
                with transaction.atomic():
                    if Customer.objects.filter(email=data.email).exists():
                        errors.append(f"Record {i}: Email {data.email} already exists")
                        continue
                    if data.phone and not re.match(r'^(\+\d+|\d{3}-\d{3}-\d{4})$', data.phone):
                        errors.append(f"Record {i}: Invalid phone format {data.phone}")
                        continue
                    c = Customer.objects.create(name=data.name, email=data.email, phone=data.phone or '')
                    created.append(c)
            except IntegrityError as e:
                errors.append(f"Record {i}: Integrity error: {str(e)}")
        return BulkCreateCustomers(customers=created, errors=errors or None)
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    product = graphene.Field(lambda: ProductNode)
    errors = graphene.List(graphene.String)
    @staticmethod
    def mutate(root, info, input):
        errs = []
        if input.price <= 0:
            errs.append('Price must be positive')
        if input.stock is not None and input.stock < 0:
            errs.append('Stock cannot be negative')
        if errs:
            return CreateProduct(product=None, errors=errs)
        p = Product.objects.create(name=input.name, price=decimal.Decimal(str(input.price)), stock=input.stock or 0)
        return CreateProduct(product=p, errors=None)
class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)
        order_date = graphene.types.datetime.DateTime()
    order = graphene.Field(lambda: OrderNode)
    errors = graphene.List(graphene.String)
    @staticmethod
    def mutate(root, info, customer_id, product_ids, order_date=None):
        errs = []
        try:
            # resolve global IDs if using relay.Node format or simple int IDs
            if ':' in str(customer_id):
                # relay global id, try to get db id
                from graphql_relay import from_global_id
                customer_db_id = from_global_id(customer_id)[1]
            else:
                customer_db_id = customer_id
            customer = Customer.objects.filter(id=customer_db_id).first()
            if not customer:
                errs.append('Invalid customer ID')
                return CreateOrder(order=None, errors=errs)
            products = []
            for pid in product_ids:
                if ':' in str(pid):
                    from graphql_relay import from_global_id
                    pid_db = from_global_id(pid)[1]
                else:
                    pid_db = pid
                prod = Product.objects.filter(id=pid_db).first()
                if not prod:
                    errs.append(f'Invalid product ID: {pid}')
                else:
                    products.append(prod)
            if not products:
                errs.append('At least one valid product is required')
                return CreateOrder(order=None, errors=errs)
            # create order and order items, calculate total
            with transaction.atomic():
                order = Order.objects.create(customer=customer, order_date=order_date or datetime.datetime.utcnow())
                total = decimal.Decimal('0')
                for prod in products:
                    OrderItem.objects.create(order=order, product=prod, quantity=1)
                    total += prod.price
                order.total_amount = total
                order.save()
            return CreateOrder(order=order, errors=None)
        except Exception as e:
            return CreateOrder(order=None, errors=[str(e)])
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class Query(graphene.ObjectType):
    all_customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType)

    def resolve_all_customers(root, info):
        return Customer.objects.all()

class UpdateLowStockProducts(graphene.Mutation):
    success = graphene.Boolean()
    updated_products = graphene.List(graphene.String)

    def mutate(self, info):
        updated = []
        for product in Product.objects.filter(stock__lt=10):
            product.stock += 10
            product.save()
            updated.append(f"{product.name} -> {product.stock}")
        return UpdateLowStockProducts(success=True, updated_products=updated)

class Mutation(graphene.ObjectType):
    update_low_stock_products = UpdateLowStockProducts.Field()


