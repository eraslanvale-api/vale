from django.contrib import admin
from .models import Order, OrderStop

class OrderStopInline(admin.TabularInline):
    model = OrderStop
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service', 'status', 'pickup_time', 'price')
    list_filter = ('status', 'service', 'pickup_time')
    search_fields = ('id', 'user__email', 'pickup_address', 'dropoff_address')
    inlines = [OrderStopInline]
