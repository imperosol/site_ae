from django.urls import path

from .api.basket import create_basket, delete_basket, validate_basket
from .views import *

app_name = 'eboutique'
urlpatterns = [
    path('', index, name='index'),
    path('basket/create/', create_basket, name='create_basket'),
    path('basket/delete/', delete_basket, name='delete_basket'),
    path('basket/validate/', validate_basket, name='validate_basket'),
    path('get/amount_sold/<int:product_id>', get_amount_sold, name='get_amount_sold'),
]
