from django.urls import path
from . import views

app_name = 'user_management'

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('<int:pk>/edit/', views.team_member_edit, name='team_member_edit'),
]
