import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter

class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node, )
        # Enable ordering
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'email': ['exact', 'icontains'],
        }

class ProductNode(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node, )
        filter_fields = ['name', 'price', 'stock']

class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node, )
        filter_fields = ['total_amount', 'order_date']

class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerNode, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductNode, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderNode, filterset_class=OrderFilter)
