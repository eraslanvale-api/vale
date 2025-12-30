from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ImportExportModelAdmin
from .models import User, Address, PushToken, ExpoPushToken, Invoice

class CustomUserAdmin(ImportExportModelAdmin, UserAdmin):
    model = User
    list_display = ('email', 'full_name', 'phone_number', 'role', 'is_verified', 'is_staff', 'is_active')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'full_name', 'phone_number')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Kişisel Bilgiler', {'fields': ('full_name', 'phone_number', 'role')}),
        ('Doğrulama Durumu', {'fields': ('is_verified', 'verification_code', 'verification_code_sent_at', 'password_reset_code', 'password_reset_code_sent_at')}),
        ('İzinler', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Tarih Bilgileri', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'full_name', 'phone_number', 'role'),
        }),
    )

@admin.register(Address)
class AddressAdmin(ImportExportModelAdmin):
    list_display = ('user', 'title', 'city_district', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('user__email', 'title', 'description', 'lat', 'lng')
    
    def city_district(self, obj):
        # Eğer modelde city/district yoksa description veya title gösterilebilir.
        # Address modelinde city/district yok, sadece title/description var.
        return f"{obj.title} - {obj.description}"
    city_district.short_description = "Adres Detayı"

@admin.register(Invoice)
class InvoiceAdmin(ImportExportModelAdmin):
    list_display = ('user', 'invoice_type', 'full_name', 'city', 'district', 'is_default')
    list_filter = ('invoice_type', 'is_default')
    search_fields = ('user__email', 'full_name', 'email', 'phone_number', 'city', 'district')

@admin.register(PushToken)
class PushTokenAdmin(ImportExportModelAdmin):
    list_display = ('user', 'platform', 'short_token', 'created_at')
    list_filter = ('platform', 'created_at')
    search_fields = ('user__email', 'token')

    def short_token(self, obj):
        return obj.token[:20] + "..." if obj.token else "-"
    short_token.short_description = "Token (Kısaltılmış)"

@admin.register(ExpoPushToken)
class ExpoPushTokenAdmin(ImportExportModelAdmin):
    list_display = ('user', 'short_token', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'token')

    def short_token(self, obj):
        return obj.token[:20] + "..." if obj.token else "-"
    short_token.short_description = "Token (Kısaltılmış)"

# User modelini CustomUserAdmin ile register et
admin.site.register(User, CustomUserAdmin)
