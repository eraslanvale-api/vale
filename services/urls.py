from django.urls import path
from .views import ServiceListView, ServiceDetailView, ServiceBySlugView

urlpatterns = [
    path('services/', ServiceListView.as_view(), name='service_list'),
    path('services/<uuid:id>/', ServiceDetailView.as_view(), name='service_detail'),
    path('services/slug/<slug:slug>/', ServiceBySlugView.as_view(), name='service_detail_by_slug'),
]
