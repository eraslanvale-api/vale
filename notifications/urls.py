from django.urls import path
from .views import NotificationListView, NotificationDetailView, MarkAllReadView

urlpatterns = [
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/<uuid:id>/', NotificationDetailView.as_view(), name='notification_detail'),
    path('notifications/mark-all-read/', MarkAllReadView.as_view(), name='mark_all_read'),
]
