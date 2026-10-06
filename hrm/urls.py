from django.urls import path
from . import views

app_name = 'hrm'

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('departments/', views.department_manage, name='department_manage'),
]
