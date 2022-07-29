from django.urls import path

from .views import *

app_name = 'eboutique'
urlpatterns = [
    path('', index, name='index'),
    path('create_basket/', create_basket, name='create_basket'),
    path('delete_basket/', delete_basket, name='delete_basket'),
]
