from django.urls import path
from .views import NotificationListView, NotificationDetailView, MarkAllReadView, UpdatePushTokenView

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<uuid:id>/', NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/mark-all-read/', MarkAllReadView.as_view(), name='mark_all_read'),
    path('notifications/update-push-token/', UpdatePushTokenView.as_view(), name='update_push_token'),
]
