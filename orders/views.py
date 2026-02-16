from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
from .models import Order, VehicleHandoverPhoto
from .serializers import OrderSerializer, EmergencyAlertSerializer, VehicleHandoverPhotoSerializer
from notifications.models import Notification
from accounts.models import User

class EmergencyAlertCreateView(generics.CreateAPIView):
    serializer_class = EmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        alert = serializer.save(user=self.request.user)
        # Notify admins
        admins = User.objects.filter(role='Yönetici', is_active=True)
        message = f"{alert.user.full_name or alert.user.email} tarafından acil durum bildirimi gönderildi!"
        for admin in admins:
            Notification.objects.create(
                user=admin,
                title="🚨 ACİL DURUM BİLDİRİMİ",
                message=message
            )

class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Müşteri sadece kendi siparişlerini görür
        queryset = Order.objects.filter(user=self.request.user).order_by('-created_at')
        
        status_group = self.request.query_params.get('group')
        if status_group == 'active':
            queryset = queryset.filter(status__in=[
                'scheduled', 'searching', 'accepted', 'assigned', 'on_way', 'in_progress'
            ])
        elif status_group == 'history':
            queryset = queryset.filter(status__in=['completed', 'cancelled'])
            
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'Şoför':
            serializer.save(user=user, driver=user, status='assigned')
        else:
            serializer.save(user=user)


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        # Müşteri kendi siparişini, Sürücü atandığı veya havuzdaki siparişi görebilir
        user = self.request.user
        if user.role == 'Şoför': # Driver rolü kontrolü
             return Order.objects.all() # Sürücüler detay görebilsin (daha kısıtlı bir filtre eklenebilir)
        return Order.objects.filter(user=user)

class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            # Sadece kendi siparişini iptal edebilir
            order = Order.objects.get(id=id, user=request.user)
            
            # İptal edilemeyecek durumlar
            if order.status in ['completed', 'cancelled', 'in_progress']:
                return Response(
                    {"error": "Bu sipariş artık iptal edilemez (Tamamlanmış veya Sürüşte)."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Diğer tüm durumlarda (scheduled, searching, assigned, accepted, on_way) iptal edilebilir
            order.status = 'cancelled'
            order.save()

            # Notify admins
            admins = User.objects.filter(role='Yönetici', is_active=True)
            message = f"#{order.id} nolu rezervasyon müşteri tarafından iptal edildi."
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    title="❌ Rezervasyon İptal Edildi",
                    message=message
                )

            return Response(OrderSerializer(order).data)
            
        except Order.DoesNotExist:
            return Response({"error": "Sipariş bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

# --- Driver Views ---

class DriverJobPoolView(generics.ListAPIView):
    """
    Sürücülerin havuzdaki (henüz atanmamış) işleri göreceği endpoint.
    ARTIK SADECE ATANMIŞ İŞLERİ DÖNDÜRÜR (Havuz iptal edildi).
    Mobil uyumluluğu bozulmasın diye endpoint duruyor ama mantık değişti.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Eski Mantık: status=['scheduled', 'searching'] ve driver=None
        # Yeni Mantık: Sadece bana atanmış işler (Havuz kapalı)
        return Order.objects.filter(
            status__in=['scheduled', 'searching', 'assigned', 'accepted', 'on_way', 'in_progress'], 
            driver=self.request.user
        ).order_by('created_at')

class DriverMyJobsView(generics.ListAPIView):
    """
    Sürücünün kendi üstlendiği veya tamamladığı işler.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Sadece bu sürücüye atanmış tüm işler (Tamamlananlar dahil)
        # Ek güvenlik: Eğer driver=None ise (sahipsiz) veya başkasına atanmışsa getirmemeli.
        # Filtre: (scheduled OR searching OR assigned OR accepted OR on_way OR in_progress OR completed OR cancelled) AND driver=request.user
        return Order.objects.filter(
            status__in=['scheduled', 'searching', 'assigned', 'accepted', 'on_way', 'in_progress', 'completed', 'cancelled'], 
            driver=self.request.user
        ).order_by('-created_at')

class DriverAcceptJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            with transaction.atomic():
                # Select for update ile kilitleyelim ki aynı anda iki kişi alamasın
                order = Order.objects.select_for_update().get(id=id)
                
                # Eğer sürücü zaten atanmışsa ve bu kişi ben değilsem hata ver
                if order.driver is not None and order.driver != request.user:
                    return Response(
                        {"error": "Bu görev başka bir sürücü tarafından alınmış."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Eğer sürücü atanmamışsa veya bana atanmışsa kabul et
                order.driver = request.user
                order.status = 'on_way' # Direkt Yola Çıktım (Kısaltılmış Akış)
                order.save()
                
                return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Görev bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

class DriverOnWayView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            order = Order.objects.get(id=id, driver=request.user)
            # Sadece accepted durumundan on_way durumuna geçebilir
            if order.status != 'accepted':
                return Response({"error": "Sipariş henüz kabul edilmemiş."}, status=status.HTTP_400_BAD_REQUEST)
            
            order.status = 'on_way'
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Görev bulunamadı veya size ait değil."}, status=status.HTTP_404_NOT_FOUND)

class DriverStartJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            order = Order.objects.get(id=id, driver=request.user)
            # Sadece on_way durumundan in_progress durumuna geçebilir
            if order.status != 'on_way':
                return Response({"error": "Henüz yolda değilsiniz."}, status=status.HTTP_400_BAD_REQUEST)
            
            # OPSİYONEL KONTROL: Araç teslim fotoğrafları yüklenmiş mi?
            # Kullanıcı isteği üzerine zorunluluk kaldırıldı.
            # 4 adet fotoğraf olmalı (ön, arka, sağ, sol)
            # photo_count = VehicleHandoverPhoto.objects.filter(order=order).count()
            # if photo_count < 4:
            #     return Response(
            #         {"error": "Lütfen yolculuğa başlamadan önce aracın 4 farklı açıdan fotoğrafını yükleyiniz."}, 
            #         status=status.HTTP_400_BAD_REQUEST
            #     )
            
            order.status = 'in_progress'
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Görev bulunamadı veya size ait değil."}, status=status.HTTP_404_NOT_FOUND)

class DriverCompleteJobView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        try:
            order = Order.objects.get(id=id, driver=request.user)
            order.status = 'completed'
            order.save()
            return Response(OrderSerializer(order).data)
        except Order.DoesNotExist:
            return Response({"error": "Görev bulunamadı veya size ait değil."}, status=status.HTTP_404_NOT_FOUND)

class VehicleHandoverPhotoCreateView(generics.CreateAPIView):
    serializer_class = VehicleHandoverPhotoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Aynı sipariş ve tip için daha önce fotoğraf varsa sil (Overwrite mantığı)
        order_id = request.data.get('order')
        photo_type = request.data.get('photo_type')
        
        if order_id and photo_type:
            VehicleHandoverPhoto.objects.filter(order_id=order_id, photo_type=photo_type).delete()
            
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Sadece sürücü yükleyebilir kontrolü eklenebilir
        # Burada order'a erişip driver kontrolü yapabiliriz
        order_id = self.request.data.get('order')
        # Basitlik için şimdilik sadece kaydediyoruz, order sahipliği kontrolü serializer veya permission'da yapılabilir
        serializer.save()
