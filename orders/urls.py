from django.urls import path
from .views import (
    OrderListView, 
    OrderDetailView, 
    DriverJobPoolView, 
    DriverMyJobsView, 
    DriverAcceptJobView,
    DriverCompleteJobView,
    OrderCancelView,
    DriverOnWayView,
    DriverStartJobView,
    EmergencyAlertCreateView
)

urlpatterns = [
    path('emergency-alert/', EmergencyAlertCreateView.as_view(), name='emergency-alert-create'),
    path('', OrderListView.as_view(), name='order_list'),
    path('driver/pool/', DriverJobPoolView.as_view(), name='driver-job-pool'),
    path('driver/my-jobs/', DriverMyJobsView.as_view(), name='driver-my-jobs'),
    path('<str:id>/accept/', DriverAcceptJobView.as_view(), name='driver-accept-job'),
    path('<str:id>/on-way/', DriverOnWayView.as_view(), name='driver-on-way'),
    path('<str:id>/start/', DriverStartJobView.as_view(), name='driver-start-job'),
    path('<str:id>/complete/', DriverCompleteJobView.as_view(), name='driver-complete-job'),
    path('<str:id>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('<str:id>/', OrderDetailView.as_view(), name='order_detail'),
]
