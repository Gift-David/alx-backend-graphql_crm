import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Customer, Product, Order

# --- Types ---

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class OrderType(DjangoObjectType):
    class Meta:
        model = Order

# --- Input Objects ---

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

# --- Mutations ---

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        # 1. Email Uniqueness Validation
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists")
        
        # 2. Phone Validation
        if phone:
            phone_validator = RegexValidator(regex=r'^(\+\d{1,3})?\d{3}-?\d{3}-?\d{4}$')
            try:
                phone_validator(phone)
            except ValidationError:
                raise Exception("Invalid phone format")

        customer = Customer.objects.create(name=name, email=email, phone=phone)
        return CreateCustomer(customer=customer, success=True, message="Customer created successfully")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers_data = graphene.List(CustomerInput, required=True)

    created_customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers_data):
        success_list = []
        error_list = []

        for data in customers_data:
            try:
                with transaction.atomic():
                    # Validate
                    if Customer.objects.filter(email=data.email).exists():
                        raise ValidationError(f"Email {data.email} already exists")
                    
                    c = Customer.objects.create(
                        name=data.name, 
                        email=data.email, 
                        phone=data.get('phone')
                    )
                    success_list.append(c)
            except Exception as e:
                error_list.append(str(e))

        return BulkCreateCustomers(created_customers=success_list, errors=error_list)

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be a positive decimal")
        if stock < 0:
            raise Exception("Stock cannot be negative")
        
        product = Product.objects.create(name=name, price=price, stock=stock)
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        # 1. Validations
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        if not product_ids:
            raise Exception("At least one product must be selected")

        products = Product.objects.filter(id__in=product_ids)
        if products.count() != len(product_ids):
            raise Exception("One or more product IDs are invalid")

        # 2. Behavior: Create Order and Calculate total_amount
        with transaction.atomic():
            total = sum([p.price for p in products])
            order = Order.objects.create(customer=customer, total_amount=total)
            order.products.set(products)
            order.save()

        return CreateOrder(order=order)

# --- Root Mutation ---

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()