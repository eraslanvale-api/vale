from rest_framework import status, views, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from accounts.models import User
from accounts.serializers import UserSerializer
from orders.models import Order
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from notifications.models import Notification
from notifications.utils import send_expo_push_notification, send_html_email
import threading

class DashboardLoginView(views.APIView):
    """
    Sadece yönetici rolüne sahip kullanıcıların pano (dashboard) girişi yapmasını sağlar.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({"detail": "E-posta ve şifre zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                if user.role != 'Yönetici':
                    return Response({"detail": "Sadece yöneticiler bu alana giriş yapabilir."}, status=status.HTTP_403_FORBIDDEN)
                
                if not user.is_active:
                    return Response({"detail": "Heseabınız pasif durumdadır."}, status=status.HTTP_403_FORBIDDEN)

                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key,
                    "user": UserSerializer(user).data
                })
            else:
                return Response({"detail": "Girdiğiniz şifre hatalı."}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"detail": "Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

class DashboardStatsView(views.APIView):
    """
    Pano için gerçek zamanlı istatistikleri döner.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'Yönetici':
            return Response({"detail": "Bu işlem için yetkiniz bulunmamaktadır."}, status=status.HTTP_403_FORBIDDEN)

        # Toplam Rezervasyon
        total_reservations = Order.objects.count()
        
        # Bekleyen Rezervasyonlar (Sürücü Atanmamış olanlar)
        # Sadece tamamlanmamış ve iptal edilmemiş olanları sayalım
        waiting_reservations = Order.objects.filter(
            driver__isnull=True
        ).exclude(status__in=['completed', 'cancelled']).count()
        
        # Aktif İşler
        active_rides = Order.objects.filter(
            status__in=['searching', 'assigned', 'accepted', 'on_way', 'in_progress']
        ).count()

        # Tamamlanan Rezervasyonlar
        completed_reservations = Order.objects.filter(status='completed').count()

        # İptal Edilen Rezervasyonlar
        cancelled_reservations = Order.objects.filter(status='cancelled').count()

        # Aktif Acil Durum Bildirimleri
        active_emergency_alerts = EmergencyAlert.objects.filter(is_resolved=False).count()

        # Toplam Araç Fotoğrafı
        total_photos = VehicleHandoverPhoto.objects.count()

        return Response({
            "total_reservations": total_reservations,
            "waiting_reservations": waiting_reservations,
            "active_rides": active_rides,
            "completed_reservations": completed_reservations,
            "cancelled_reservations": cancelled_reservations,
            "active_emergency_alerts": active_emergency_alerts,
            "total_photos": total_photos,
        })

class WaitingReservationsListView(views.APIView):
    """
    Sürücü atanmamış bekleyen rezervasyonları listeler.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'Yönetici':
            return Response({"detail": "Bu işlem için yetkiniz bulunmamaktadır."}, status=status.HTTP_403_FORBIDDEN)
        
        orders = Order.objects.filter(
            driver__isnull=True
        ).exclude(status__in=['completed', 'cancelled']).order_by('-created_at')
        
        from orders.serializers import OrderSerializer
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)



from rest_framework import viewsets
from rest_framework.decorators import action
from orders.serializers import OrderSerializer
from orders.models import EmergencyAlert, VehicleHandoverPhoto
from services.models import Service, Vehicle
from .serializers import (
    DashboardOrderSerializer, 
    DashboardUserSerializer, 
    DashboardEmergencyAlertSerializer,
    DashboardOrderPhotoGallerySerializer,
    DashboardServiceSerializer,
    DashboardVehicleSerializer
)

class DashboardOrderViewSet(viewsets.ModelViewSet):
    """
    Yöneticiler için tüm siparişlerin CRUD işlemlerini sağlar.
    """
    serializer_class = DashboardOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'Yönetici':
            return Order.objects.none()
        return Order.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        order = serializer.save()
        # Send notifications to admins in background thread
        threading.Thread(target=self._notify_admins, args=(order,)).start()
    
    def _notify_admins(self, order):
        """Send email and push notifications to all admin users."""
        try:
            admins = User.objects.filter(role='Yönetici', is_active=True)
            
            # Prepare notification content
            customer_name = order.user.full_name or order.user.email or order.user.phone_number if order.user else 'Bilinmiyor'
            service_name = order.service.name if order.service else 'Bilinmiyor'
            pickup_time = order.pickup_time.strftime('%d.%m.%Y %H:%M') if order.pickup_time else 'Belirtilmemiş'
            
            subject = f'🚗 Yeni Rezervasyon Oluşturuldu - #{order.id}'
            message = f"""
Yeni bir rezervasyon oluşturuldu.

📋 Rezervasyon Detayları:
━━━━━━━━━━━━━━━━━━━━━━━━
🆔 Rezervasyon No: #{order.id}
👤 Müşteri: {customer_name}
🚗 Hizmet: {service_name}
📍 Başlangıç: {order.pickup or 'Belirtilmemiş'}
🏁 Varış: {order.dropoff or 'Belirtilmemiş'}
📅 Tarih/Saat: {pickup_time}
💰 Tutar: ₺{order.price or 0}
📏 Mesafe: {order.distance_km or 0} km

━━━━━━━━━━━━━━━━━━━━━━━━
Premium Vale Yönetim Paneli
            """
            
            # Send email to admins with valid email addresses
            admin_emails = [admin.email for admin in admins if admin.email]
            if admin_emails:
                send_html_email(
                    subject=subject,
                    message=message.strip(),
                    recipient_list=admin_emails
                )
                print(f"Admin email notification sent to: {admin_emails}")
            
            # Send push notifications to admins with push tokens
            push_tokens = [admin.expo_push_token for admin in admins if admin.expo_push_token]
            if push_tokens:
                try:
                    send_expo_push_notification(
                        tokens=push_tokens,
                        title='🚗 Yeni Rezervasyon',
                        message=f'{customer_name} - {service_name} - ₺{order.price or 0}',
                        data={'type': 'new_order', 'order_id': order.id},
                        sound='notification.wav',
                        channel_id='premium_alert'
                    )
                    print(f"Admin push notification sent to {len(push_tokens)} admins")
                except Exception as e:
                    print(f"Push notification error: {e}")
            
            # Create in-app notifications for admins
            detail_message = f"{customer_name} tarafından {pickup_time} için {service_name} rezervasyonu oluşturuldu."
            for admin in admins:
                try:
                    Notification.objects.create(
                        user=admin,
                        title=f"New Reservation - #{order.id}",
                        message=detail_message
                    )
                except Exception as e:
                    print(f"Admin in-app notify error for user {admin.id}: {e}")
        except Exception as e:
            print(f"Admin notification error: {e}")

    @action(detail=True, methods=['post'], url_path='assign-driver')
    def assign_driver(self, request, pk=None):
        """Assign a driver and optionally a vehicle to the order and notify the driver."""
        order = self.get_object()
        driver_id = request.data.get('driver_id')
        vehicle_id = request.data.get('vehicle_id')
        
        if not driver_id:
            return Response({"detail": "driver_id gereklidir."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            driver = User.objects.get(id=driver_id, role='Şoför')
        except User.DoesNotExist:
            return Response({"detail": "Şoför bulunamadı."}, status=status.HTTP_404_NOT_FOUND)
        
        # Assign driver
        order.driver = driver
        order.status = 'assigned'
        
        # Optionally assign vehicle
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, is_active=True)
                order.vehicle = vehicle
                order.license_plate = vehicle.plate
            except Vehicle.DoesNotExist:
                return Response({"detail": "Araç bulunamadı veya aktif değil."}, status=status.HTTP_404_NOT_FOUND)
        
        order.save()
        
        # Notify driver in background
        threading.Thread(target=self._notify_driver, args=(order, driver)).start()
        
        return Response({
            "detail": "Atama başarıyla tamamlandı.", 
            "order_id": order.id, 
            "driver_id": driver.id,
            "vehicle_id": vehicle_id
        })
    
    def _notify_driver(self, order, driver):
        """Send push notification and email to the assigned driver."""
        try:
            customer_name = order.user.full_name or order.user.email or order.user.phone_number if order.user else 'Bilinmiyor'
            pickup_time = order.pickup_time.strftime('%d.%m.%Y %H:%M') if order.pickup_time else 'Belirtilmemiş'
            
            # Send push notification
            if driver.expo_push_token:
                try:
                    send_expo_push_notification(
                        tokens=[driver.expo_push_token],
                        title='🚗 Yeni İş Atandı!',
                        message=f'{customer_name} - {order.pickup or "Konum"} → {order.dropoff or "Konum"} - ₺{order.price or 0}',
                        data={'type': 'job_assigned', 'order_id': order.id}
                    )
                    print(f"Driver push notification sent to: {driver.email}")
                except Exception as e:
                    print(f"Driver push notification error: {e}")
            
            # Send email
            if driver.email:
                try:
                    subject = f'🚗 Yeni İş Atandı - #{order.id}'
                    message = f"""
Merhaba {driver.full_name or driver.email},

Size yeni bir iş atandı!

📋 Rezervasyon Detayları:
━━━━━━━━━━━━━━━━━━━━━━━━
🆔 Rezervasyon No: #{order.id}
👤 Müşteri: {customer_name}
📍 Başlangıç: {order.pickup or 'Belirtilmemiş'}
🏁 Varış: {order.dropoff or 'Belirtilmemiş'}
📅 Tarih/Saat: {pickup_time}
💰 Tutar: ₺{order.price or 0}
📏 Mesafe: {order.distance_km or 0} km

Lütfen uygulamayı açarak işi onaylayın.

━━━━━━━━━━━━━━━━━━━━━━━━
Premium Vale
                    """
                    send_html_email(
                        subject=subject,
                        message=message.strip(),
                        recipient_list=[driver.email]
                    )
                    print(f"Driver email notification sent to: {driver.email}")
                except Exception as e:
                    print(f"Driver email notification error: {e}")
                    
        except Exception as e:
            print(f"Driver notification error: {e}")


class DashboardUserViewSet(viewsets.ModelViewSet):
    """
    Yöneticiler için tüm kullanıcıların CRUD işlemlerini sağlar.
    """
    serializer_class = DashboardUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'Yönetici':
            return User.objects.none()
        
        # Restore aksiyonu için her zaman tüm kullanıcıları (silinenler dahil) döndür
        if self.action == 'restore':
            return User.objects.all()

        # is_active filtresi (null=aktifler, false=silinenler, true=hepsi)
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            if is_active.lower() == 'false':
                queryset = User.objects.filter(is_active=False)
            elif is_active.lower() == 'true':
                queryset = User.objects.filter(is_active=True)
            else:
                queryset = User.objects.all()
        else:
            queryset = User.objects.filter(is_active=True)

        queryset = queryset.order_by('-date_joined')
        
        # Arama parametresi
        query = self.request.query_params.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(full_name__icontains=query)
            )
        
        # Rol filtresi
        role = self.request.query_params.get('role', '')
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset

    def perform_destroy(self, instance):
        """Kullanıcıyı veritabanından silmek yerine pasif hale getirir (Soft Delete)."""
        if instance.role == 'Yönetici':
            # Viewset içinden hata fırlatmak Response dönmekten daha güvenlidir
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Yönetici hesapları silinemez.")
            
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['post'], url_path='restore')
    def restore(self, request, pk=None):
        """Silinmiş (pasif) kullanıcıyı yeniden aktif hale getirir."""
        user = self.get_object()
        if user.is_active:
            return Response({"detail": "Kullanıcı zaten aktif."}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_active = True
        user.save()
        return Response({"detail": "Kullanıcı başarıyla geri yüklendi.", "id": user.id})


class DashboardEmergencyAlertViewSet(viewsets.ModelViewSet):
    """
    Yöneticiler için acil durum bildirimlerinin yönetimi.
    """
    serializer_class = DashboardEmergencyAlertSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role != 'Yönetici':
            return EmergencyAlert.objects.none()
        
        queryset = EmergencyAlert.objects.all().select_related('order', 'user', 'order__driver').order_by('-created_at')
        
        # Filter by resolved status
        is_resolved = self.request.query_params.get('is_resolved', None)
        if is_resolved is not None:
            queryset = queryset.filter(is_resolved=is_resolved.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        """Mark emergency alert as resolved."""
        alert = self.get_object()
        alert.is_resolved = True
        alert.save()
        return Response({
            "detail": "Acil durum bildirimi çözüldü olarak işaretlendi.",
            "id": alert.id
        })
    
    @action(detail=True, methods=['post'], url_path='unresolve')
    def unresolve(self, request, pk=None):
        """Mark emergency alert as unresolved (reopen)."""
        alert = self.get_object()
        alert.is_resolved = False
        alert.save()
        return Response({
            "detail": "Acil durum bildirimi yeniden açıldı.",
            "id": alert.id
        })


class DashboardOrderPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Fotoğrafı olan siparişlerin listelenmesi ve görüntülenmesi.
    """
    serializer_class = DashboardOrderPhotoGallerySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'Yönetici':
            return Order.objects.none()
        
        # Sadece fotoğrafı olan siparişleri getir
        return Order.objects.filter(handover_photos__isnull=False).distinct().order_by('-created_at')


class DashboardServiceViewSet(viewsets.ModelViewSet):
    """
    Hizmetlerin (Servislerin) yönetimi.
    """
    serializer_class = DashboardServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'Yönetici':
            return Service.objects.none()
        return Service.objects.all().order_by('name')


class DashboardVehicleViewSet(viewsets.ModelViewSet):
    """
    Araçların (Vehicles) yönetimi.
    """
    serializer_class = DashboardVehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role != 'Yönetici':
            return Vehicle.objects.none()
        
        queryset = Vehicle.objects.all().order_by('plate')
        
        query = self.request.query_params.get('q', '')
        if query:
            queryset = queryset.filter(
                Q(plate__icontains=query) |
                Q(brand__icontains=query) |
                Q(model__icontains=query)
            )
            
        return queryset

def send_bulk_notifications_background(user_ids, group, title, message, channels):
    """
    Bildirimleri arka planda gönderen yardımcı fonksiyon.
    HTML Email Template içerir.
    """
    users = User.objects.filter(is_active=True)
    if user_ids:
        users = users.filter(id__in=user_ids)
    elif group == 'driver':
        users = users.filter(role='Şoför')
    elif group == 'customer':
        users = users.filter(role='Müşteri')
    
    emails = []
    push_tokens = []
    
    for user in users:
        if 'email' in channels and user.email:
            emails.append(user.email)
        
        if 'push' in channels:
            # User ile ilişkili tüm ExpoPushToken'ları al
            tokens = user.expo_push_tokens.values_list('token', flat=True)
            push_tokens.extend(tokens)

    # Toplu E-posta (HTML Template)
    if 'email' in channels and emails:
        send_html_email(
            subject=title,
            message=message,
            recipient_list=emails
        )

    # Toplu Push Bildirimi
    if 'push' in channels and push_tokens:
        try:
            send_expo_push_notification(
                tokens=push_tokens,
                title=title,
                message=message
            )
        except Exception as e:
            print(f"Bulk push error: {e}")

class BulkNotificationView(views.APIView):
    """
    Yöneticilerin kullanıcılara toplu bildirim göndermesini sağlar.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'Yönetici':
            return Response({"detail": "Yalnızca yöneticiler bildirim gönderebilir."}, status=status.HTTP_403_FORBIDDEN)

        title = request.data.get('title')
        message = request.data.get('message')
        channels = request.data.get('channels', [])
        user_ids = request.data.get('user_ids') # Liste veya null
        group = request.data.get('group', 'all') # all, driver, customer

        if not title or not message:
            return Response({"detail": "Başlık ve mesaj zorunludur."}, status=status.HTTP_400_BAD_REQUEST)

        if not channels:
            return Response({"detail": "En az bir gönderim kanalı seçilmelidir."}, status=status.HTTP_400_BAD_REQUEST)

        # Arka planda işlemi başlat
        import threading
        threading.Thread(
            target=send_bulk_notifications_background, 
            args=(user_ids, group, title, message, channels)
        ).start()

        return Response({"detail": "Bildirim gönderim işlemi arka planda başlatıldı."})
