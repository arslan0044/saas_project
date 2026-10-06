from django.db import models

class Lead(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('lost', 'Lost'),
    ]
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.company_name}"