from django.urls import path
from . import views
from . import api

app_name = 'pedagogy'
urlpatterns = [
    path('uvs/', views.uv_search, name='uv_search'),
    path('uvs/<str:uv_code>/', views.uv_detail, name='uv_detail'),

    # api
    path('api/category/reset', api.reset_categories, name='reset_categories'),
    path('api/filiere/reset', api.reset_filieres, name='reset_filieres'),
    path('api/uv/reset', api.reset_uvs, name='reset_uvs'),
]
