from django.urls import path

import pedagogy.api
from . import api
from . import views

app_name = 'pedagogy'
urlpatterns = [
    path('uvs/', views.uv_search, name='uv_search'),
    path('uvs/<str:uv_code>/', views.uv_detail, name='uv_detail'),
    path('uvs/<int:uv_id>/my-review/', views.review_html_fragment, name='review_html_fragment'),
    path('uvs/<int:uv_id>/grades/', views.uv_grades_fragment, name='uv_grades_fragment'),
    path('uvs/<int:uv_id>/annals/add', views.annale_add, name='annale_add'),

    # api
    path('api/review/register/', pedagogy.api.register_review, name='register_review'),
    path('api/review/<int:review_id>/validate/', api.review_validate, name='review_validate'),
    path('api/review/<int:review_id>/delete/', api.review_delete, name='review_delete'),
    path('api/category/reset/', api.reset_categories, name='reset_categories'),
    path('api/filiere/reset/', api.reset_filieres, name='reset_filieres'),
    path('api/uv/reset/', api.reset_uvs, name='reset_uvs'),
    path('api/uv/list/', api.get_uvs, name='get_uvs'),
    path('api/annal/<int:annal_id>/download/', api.download_annal, name='download_annal'),
    path('api/annal/<int:annal_id>/delete/', api.delete_annal, name='delete_annal'),
    path('api/annal/<int:annal_id>/approve/', api.approve_annal, name='approve_annal'),
]
