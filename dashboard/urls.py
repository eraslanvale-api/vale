from django.urls import path, include
from .views import (
    DashboardLoginView, DashboardStatsView, WaitingReservationsListView, 
    DashboardOrderViewSet, DashboardUserViewSet, DashboardEmergencyAlertViewSet,
    DashboardOrderPhotoViewSet, DashboardServiceViewSet, DashboardVehicleViewSet,
    BulkNotificationView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'orders', DashboardOrderViewSet, basename='dashboard_orders')
router.register(r'users', DashboardUserViewSet, basename='dashboard_users')
router.register(r'emergency-alerts', DashboardEmergencyAlertViewSet, basename='dashboard_emergency_alerts')
router.register(r'order-photos', DashboardOrderPhotoViewSet, basename='dashboard_order_photos')
router.register(r'services', DashboardServiceViewSet, basename='dashboard_services')
router.register(r'vehicles', DashboardVehicleViewSet, basename='dashboard_vehicles')

urlpatterns = [
    path('login/', DashboardLoginView.as_view(), name='dashboard_login'),
    path('stats/', DashboardStatsView.as_view(), name='dashboard_stats'),
    path('waiting-reservations/', WaitingReservationsListView.as_view(), name='waiting_reservations_list'),
    path('notifications/send/', BulkNotificationView.as_view(), name='bulk_notification_send'),
    path('', include(router.urls)),
]
