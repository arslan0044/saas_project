from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class TenantUserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Tenant Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tenant_profile')
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"