from django.db import models

# Create your models here.
from django_tenants.models import TenantMixin, DomainMixin

class Tenant(TenantMixin):
    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    # UI Feature Gating k liye active modules list
    active_modules = models.JSONField(default=list, blank=True)

    # True agar har tenant ka schema auto-create karna ho
    auto_create_schema = True

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    pass