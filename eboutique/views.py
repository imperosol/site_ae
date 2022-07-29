import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from site_ae.settings import MAX_MONEY_ON_ACCOUNT
from .models import Product, Discount, Balance, ProductGroup, Basket, BasketItem, Combination


# Create your views here.

@login_required
@require_GET
def index(request):
    product_groups = ProductGroup.objects.all()
    products = Product.objects.order_by('category').values('id', 'price', 'name', 'image', 'description')
    balance = Balance.objects.get_or_create(user=request.user)[0]
    discounts = Discount.objects.order_by('item__category')
    combinations = Product.objects.filter(combinations__isnull=False).values(
        'combinations__name', 'combinations__id', 'combinations__price',
        'combinations__products__name', 'combinations__products__id'
    )
    print(combinations)
    context = {
        'product_groups': product_groups,
        'products': products,
        'discounts': discounts,
        'balance': balance,
        'max_euros_more': (MAX_MONEY_ON_ACCOUNT - balance.amount) // 100,
    }
    return render(request, 'eboutique/index.html', context)


@login_required
@require_POST
def create_basket(request):
    post = json.loads(request.body)
    basket = Basket.objects.get_or_create(user=request.user)[0]
    for product_id, quantity in post['basket'].items():
        if int(quantity) > 0:
            product = Product.objects.get(pk=int(product_id))
            BasketItem.objects.update_or_create(basket=basket, product=product, quantity=quantity)
    return HttpResponse('ok')


@login_required
@require_POST
def delete_basket(request):
    BasketItem.objects.filter(basket__user=request.user).delete()
    Basket.objects.filter(user=request.user).delete()
    return HttpResponse('ok')
