
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/config/', include('config.urls')),
    path('api/services/', include('services.urls')),
    path('api/orders/', include('orders.urls')),
]
