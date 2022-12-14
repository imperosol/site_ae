from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Count
from django.http import HttpResponse, HttpResponseNotFound, HttpRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET

from site_ae.settings import MAX_MONEY_ON_ACCOUNT
from .models import Product, Discount, Balance, ProductGroup, Combination, SoldItem


# Create your views here.

@login_required
@require_GET
def index(request):
    product_groups = ProductGroup.objects.all()
    products = Product.objects.filter(category__in=product_groups).order_by('category')
    balance = Balance.objects.get_or_create(user=request.user)[0]
    discounts = Discount.objects.order_by('item__category')
    combinations = Combination.objects.distinct().annotate(num1=Count('products'))
    non_complete_combinations = [
        c.id for c in combinations if c.num1 != len(c.products.filter(id__in=products))
    ]
    combinations = combinations.exclude(id__in=non_complete_combinations)
    context = {
        'product_groups': product_groups,
        'combinations': combinations,
        'products': products,
        'discounts': discounts,
        'balance': balance,
        'max_euros_more': (MAX_MONEY_ON_ACCOUNT - balance.amount) // 100,
    }
    return render(request, 'eboutique/index.html', context)


@login_required
@require_GET
def get_amount_sold(request, product_id):
    product = Product.objects.get(pk=int(product_id))
    combinations = product.combinations.all()
    discounts = product.discount.all()
    print(combinations)
    print(product)
    total = 0

    content_type = ContentType.objects.get_for_model(Product)
    sells = SoldItem.objects.filter(item_type=content_type, item_id=product.id)
    sells = sells.aggregate(Sum('quantity'))['quantity__sum']
    total += sells if sells is not None else 0

    content_type = ContentType.objects.get_for_model(Combination)
    sells = SoldItem.objects.filter(item_type=content_type, item_id__in=combinations)
    sells = sells.aggregate(Sum('quantity'))['quantity__sum']
    total += sells if sells is not None else 0

    content_type = ContentType.objects.get_for_model(Discount)
    sells = SoldItem.objects.filter(item_type=content_type, item_id__in=discounts)
    for item in sells:
        total += item.quantity * item.item.nbr_items

    return HttpResponse(total)


@require_GET
@login_required
def get_balance(request, user_id):
    try:
        balance = Balance.objects.get(user=user_id)
        return HttpResponse(balance.amount)
    except Balance.DoesNotExist:
        return HttpResponseNotFound()
