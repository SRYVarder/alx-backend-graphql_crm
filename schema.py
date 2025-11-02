import graphene
from crm.schema import Query as CRMQuery
from crm.models import Product
class Query(CRMQuery, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)


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

