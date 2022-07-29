from django.urls import path

from . import views, api

app_name = 'vie-etu'
urlpatterns = [
    # views that render HTML
    path('club/all', views.view_all_clubs, name='view_all_clubs'),
    path('club/all/<int:page>', views.view_all_clubs, name='view_all_clubs'),
    path('club/<int:club_id>/<str:name>', views.view_detail, name='view_detail'),

    # api views that return JSON responses
    path('club/api/get', api.get_clubs, name='get_clubs'),
    path('club/api/get-club-members/<int:club_id>', api.get_club_members, name='get_club_members'),
]
