from django.urls import path
from .views import (
    OrderListView, 
    OrderDetailView, 
    DriverJobPoolView, 
    DriverMyJobsView, 
    DriverAcceptJobView,
    DriverCompleteJobView
)

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('driver/pool/', DriverJobPoolView.as_view(), name='driver-job-pool'),
    path('driver/my-jobs/', DriverMyJobsView.as_view(), name='driver-my-jobs'),
    path('<str:id>/accept/', DriverAcceptJobView.as_view(), name='driver-accept-job'),
    path('<str:id>/complete/', DriverCompleteJobView.as_view(), name='driver-complete-job'),
    path('<str:id>/', OrderDetailView.as_view(), name='order_detail'),
]
