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

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
