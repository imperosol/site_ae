import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpRequest
from django.views.decorators.http import require_POST

from eboutique.models import Basket, Product, BasketItem, Discount, Combination, Transaction, SoldItem


def __populate_discounts(basket_dict: dict[str, int], basket_model: Basket) -> None:
    discounts_objects = Discount.objects.filter(item__id__in=basket_dict.keys()).order_by('item_id', '-nbr_items')
    for d in discounts_objects:
        basket_id = str(d.item_id)
        if basket_dict[basket_id] >= d.nbr_items:
            quantity = basket_dict[basket_id] // d.nbr_items
            BasketItem(basket=basket_model, item=d, quantity=quantity).save()
            basket_dict[basket_id] %= d.nbr_items


def __populate_combinations(basket_dict: dict[str, int], basket_model: Basket) -> None:
    combinations_model = Combination.objects.filter(products__id__in=basket_dict.keys()).distinct()
    for c in combinations_model:
        products_id = [str(p.id) for p in c.products.all()]
        if any(p_id not in basket_dict for p_id in products_id):
            # Le panier ne contient pas tous les produits nécessaires pour former cette combinaison
            continue
        quantity = min(basket_dict[p_id] for p_id in products_id)
        if quantity > 0:
            BasketItem(basket=basket_model, item=c, quantity=quantity).save()
            for p_id in products_id:
                basket_dict[p_id] -= quantity


@login_required
@require_POST
def create_basket(request: HttpRequest) -> HttpResponse:
    post = json.loads(request.body)
    print(post)
    basket = Basket.objects.get_or_create(user=request.user)[0]
    BasketItem.objects.filter(basket=basket).delete()  # on vide le panier
    try:
        __populate_combinations(post['basket'], basket)
        __populate_discounts(post['basket'], basket)
        for product_id, quantity in post['basket'].items():
            if int(quantity) > 0:
                product = Product.objects.get(pk=int(product_id))
                BasketItem(basket=basket, item=product, quantity=quantity).save()
        res = json.dumps({'price': basket.total_price})
        return HttpResponse(res, content_type='application/json')
    except TypeError or KeyError:
        return HttpResponse(status=400)


@login_required
@require_POST
def validate_basket(request: HttpRequest) -> HttpResponse:
    try:
        basket = Basket.objects.get(user=request.user)
    except Basket.DoesNotExist:
        return HttpResponse(status=400, reason="Pas de panier")
    if basket.total_price > request.user.balance.amount:
        return HttpResponse(status=400, reason="Pas assez d'argent sur le compte")
    Transaction(user=request.user, amount=basket.total_price, debit_account=419, credit_account=707).save()
    for item in BasketItem.objects.filter(basket=basket):
        SoldItem.from_basket_item(item).save()
    return HttpResponse(status=200)


@login_required
@require_POST
def delete_basket(request):
    BasketItem.objects.filter(basket__user=request.user).delete()
    Basket.objects.filter(user=request.user).delete()
    return HttpResponse('ok')
