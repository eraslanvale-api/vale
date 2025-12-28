from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ConfigModel
from .serializers import ConfigSerializer

class ConfigView(APIView):
    """
    Sistemin genel konfigürasyonunu getirir.
    Eğer hiç konfigürasyon yoksa, varsayılan bir tane oluşturur.
    """
    permission_classes = [permissions.AllowAny] # Herkes konfigürasyonu okuyabilir

    def get(self, request):
        config = ConfigModel.objects.first()
        if not config:
            config = ConfigModel.objects.create()
        
        serializer = ConfigSerializer(config)
        return Response(serializer.data)

class ConfigUpdateView(generics.UpdateAPIView):
    """
    Konfigürasyonu güncellemek için (Sadece Admin).
    """
    queryset = ConfigModel.objects.all()
    serializer_class = ConfigSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_object(self):
        config = ConfigModel.objects.first()
        if not config:
            config = ConfigModel.objects.create()
        return config
