from django.urls import path
from .views import ConfigView, ConfigUpdateView

urlpatterns = [
    path('', ConfigView.as_view(), name='get_config'),
    path('update/', ConfigUpdateView.as_view(), name='update_config'),
]
