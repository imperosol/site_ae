from django.contrib import admin

from .models import Product, Basket, BasketItem, SoldItem, Balance, Transaction, Discount, \
    ProductGroup, Combination, AccountRecharge

# Register your models here.

admin_models = [
    Product, Basket, BasketItem, SoldItem, Balance, Transaction, Discount,
    ProductGroup, Combination, AccountRecharge
]

for model in admin_models:
    admin.site.register(model)
