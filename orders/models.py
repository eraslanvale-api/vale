from django.db import models
from django.conf import settings
import uuid
from services.models import Service, Vehicle

# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Planlandı'),              # Rezervasyon
        ('searching', 'Personel Aranıyor'),      # Rezervasyon → Aktif İş
        ('assigned', 'Sürücü Atandı'),           # Admin tarafından atandı
        ('accepted', 'Kabul Edildi'),            # Sürücü kabul etti
        ('on_way', 'Yolda'),                     # Sürücü müşteriye gidiyor (valet)
        ('in_progress', 'Devam Ediyor'),         # Sürüş başladı
        ('completed', 'Tamamlandı'),
        ('cancelled', 'İptal Edildi'),
    )

    id = models.CharField(primary_key=True, max_length=20, editable=False) # ORD-1024 formatında string ID
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="driver_orders")
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, related_name="orders")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    pickup_address = models.CharField(max_length=255)
    dropoff_address = models.CharField(max_length=255)

    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders", verbose_name="Atanan Araç")
    license_plate = models.CharField(max_length=20, blank=True, null=True, help_text="Otomatik olarak araçtan gelir, ancak manuel de girilebilir.")
    
    # date ve time birleştirildi
    pickup_time = models.DateTimeField()
    
    price = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    distance_km = models.FloatField()
    duration_min = models.IntegerField(default=0) # Tahmini süre (dakika)
    
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    
    dropoff_lat = models.FloatField()
    dropoff_lng = models.FloatField()
    
    invoice = models.ForeignKey('accounts.Invoice', on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="Acil Durum Kişisi")
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Acil Durum Telefonu")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.id:
            last_order = Order.objects.order_by('-created_at').first()
            if last_order and last_order.id.startswith('ORD-'):
                try:
                    last_id_num = int(last_order.id.split('-')[1])
                    new_id_num = last_id_num + 1
                except ValueError:
                    new_id_num = 1000
            else:
                new_id_num = 1000
            self.id = f"ORD-{new_id_num}"
        
        # Eğer araç seçildiyse ve plaka girilmediyse veya farklıysa, plakayı güncelle
        if self.vehicle:
            self.license_plate = self.vehicle.plate
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.user.email}"

class OrderStop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="stops")
    address = models.CharField(max_length=255)
    lat = models.FloatField()
    lng = models.FloatField()
    order_index = models.PositiveIntegerField(default=0) # order -> order_index (isim çakışmasını önlemek için)

    class Meta:
        ordering = ['order_index']

    def __str__(self):
        return f"{self.order.id} - Stop {self.order_index}: {self.address}"

class EmergencyAlert(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='emergency_alerts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='emergency_alerts_created')
    lat = models.FloatField()
    lng = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Emergency: {self.order.id} - {self.user.email}"
