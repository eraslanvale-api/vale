from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Kullanıcıya ait bildirimleri, en yeniden eskiye sıralı getir
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class NotificationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Sadece kullanıcının kendi bildirimlerine erişmesine izin ver
        return Notification.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        # Güncelleme sırasında is_read gibi alanlar güncellenebilir
        serializer.save()

class MarkAllReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Kullanıcının tüm okunmamış bildirimlerini okundu olarak işaretle
        updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": f"{updated_count} notifications marked as read."}, status=status.HTTP_200_OK)
