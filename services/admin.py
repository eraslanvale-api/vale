from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Service, Vehicle

# Register your models here.
@admin.register(Service)
class ServiceAdmin(ImportExportModelAdmin):
    list_display = ('name', 'is_active', 'show_price')
    search_fields = ('name',)
    list_filter = ('is_active', 'show_price')

@admin.register(Vehicle)
class VehicleAdmin(ImportExportModelAdmin):
    list_display = ('plate', 'brand', 'model', 'color', 'is_active')
    search_fields = ('plate', 'brand', 'model')
    list_filter = ('is_active', 'brand')
