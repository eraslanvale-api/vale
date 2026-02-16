from django.db import models
import uuid

# Create your models here.
class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=50, unique=True, help_text="Unique identifier like 'vip-vale'")
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, verbose_name="Active")
    image = models.URLField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Pricing fields
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_km = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_distance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    show_price = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

class Vehicle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plate = models.CharField(max_length=20, unique=True, verbose_name="Plaka")
    brand = models.CharField(max_length=50, blank=True, null=True, verbose_name="Marka")
    model = models.CharField(max_length=50, blank=True, null=True, verbose_name="Model")
    color = models.CharField(max_length=30, blank=True, null=True, verbose_name="Renk")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.plate} ({self.brand} {self.model})"

    class Meta:
        verbose_name = "Araç"
        verbose_name_plural = "Araçlar"
