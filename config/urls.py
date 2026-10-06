from django.contrib import admin
from django.urls import path, include
from .views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard, name='dashboard'),
    path('crm/', include('crm.urls')),
    path('hrm/', include('hrm.urls')),
    path('users/', include('user_management.urls')),
]
