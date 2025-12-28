from django.urls import path
from .views import ConfigView, ConfigUpdateView

urlpatterns = [
    path('config/', ConfigView.as_view(), name='get_config'),
    path('config/update/', ConfigUpdateView.as_view(), name='update_config'),
]
