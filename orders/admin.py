from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Order, OrderStop,EmergencyAlert

class OrderStopInline(admin.TabularInline):
    model = OrderStop
    extra = 0

@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    list_display = ('id', 'user', 'driver', 'vehicle', 'status', 'pickup_time', 'price')
    list_filter = ('status', 'service', 'pickup_time', 'vehicle')
    search_fields = ('id', 'user__email', 'driver__email', 'vehicle__plate', 'pickup_address', 'dropoff_address')
    inlines = [OrderStopInline]
    
    fieldsets = (
        ('Temel Bilgiler', {
            'fields': ('id', 'user', 'service', 'status', 'price', 'payment_method', 'invoice')
        }),
        ('Atama İşlemleri', {
            'fields': ('driver', 'vehicle', 'license_plate'),
            'description': 'Sürücü ve Araç atamasını buradan yapınız. Plaka, seçilen araçtan otomatik olarak doldurulur.'
        }),
        ('Lokasyon ve Zaman', {
            'fields': ('pickup_address', 'dropoff_address', 'pickup_time', 'distance_km', 'duration_min')
        }),
        ('Koordinatlar', {
            'fields': ('pickup_lat', 'pickup_lng', 'dropoff_lat', 'dropoff_lng'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id', 'license_plate', 'created_at', 'updated_at')

@admin.register(EmergencyAlert)
class EmergencyAlertAdmin(ImportExportModelAdmin):
    list_display = ('id', 'order', 'user', 'created_at')
    list_filter = ('order__status', 'created_at')
    search_fields = ('id', 'order__id', 'user__email', 'driver__email')
