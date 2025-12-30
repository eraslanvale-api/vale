from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import EmergencyAlert, Order

@receiver(pre_save, sender=Order)
def order_pre_save(sender, instance, **kwargs):
    """
    Sipariş kaydedilmeden önce eski durumunu kontrol et
    """
    if instance.pk:
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    Sipariş oluşturulduğunda veya durumu değiştiğinde mail gönder
    """
    should_send_email = False
    email_subject = ""
    email_title = ""
    email_message = ""
    email_color = "#000000" # Default black

    if created:
        should_send_email = True
        email_subject = f"Siparişiniz Alındı: #{instance.id}"
        email_title = "SİPARİŞİNİZ ALINDI"
        email_message = f"Sayın {instance.user.full_name or instance.user.email}, siparişiniz başarıyla oluşturulmuştur."
        email_color = "#22c55e" # Green
    elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
        if instance.status == 'cancelled':
            should_send_email = True
            email_subject = f"Sipariş İptal Edildi: #{instance.id}"
            email_title = "SİPARİŞ İPTAL EDİLDİ"
            email_message = f"Sayın {instance.user.full_name or instance.user.email}, siparişiniz iptal edilmiştir."
            email_color = "#ef4444" # Red
        elif instance.status == 'completed':
            should_send_email = True
            email_subject = f"Sipariş Tamamlandı: #{instance.id}"
            email_title = "SİPARİŞ TAMAMLANDI"
            email_message = f"Sayın {instance.user.full_name or instance.user.email}, yolculuğunuz tamamlanmıştır. Bizi tercih ettiğiniz için teşekkür ederiz."
            email_color = "#3b82f6" # Blue

    if should_send_email:
        context = {
            'title': email_title,
            'message': email_message,
            'color': email_color,
            'user_full_name': instance.user.full_name or instance.user.email,
            'order_id': str(instance.id),
            'status_label': instance.get_status_display(),
            'pickup_time': instance.pickup_time.strftime('%d.%m.%Y %H:%M'),
            'price': instance.price,
            'pickup_address': instance.pickup_address,
            'dropoff_address': instance.dropoff_address,
        }
        
        html_content = render_to_string('emails/order_notification_email.html', context)
        text_content = strip_tags(html_content)
        
        try:
            msg = EmailMultiAlternatives(
                subject=email_subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[instance.user.email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            print(f"Sipariş bildirim maili gönderildi ({instance.status}): {instance.user.email}")
        except Exception as e:
            print(f"Sipariş maili gönderilemedi: {e}")

@receiver(post_save, sender=EmergencyAlert)
def send_emergency_email_notification(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        order = instance.order
        
        # Google Maps Link
        maps_link = f"https://www.google.com/maps/search/?api=1&query={instance.lat},{instance.lng}"
        
        subject = f"ACİL DURUM: {user.full_name or user.email} Yardım Talebi Oluşturdu!"
        
        context = {
            'user_full_name': user.full_name or 'İsimsiz Kullanıcı',
            'user_phone': user.phone_number or 'Belirtilmemiş',
            'user_email': user.email,
            'order_id': str(order.id),
            'license_plate': order.license_plate or 'Belirtilmemiş',
            'order_status': order.get_status_display(),
            'lat': instance.lat,
            'lng': instance.lng,
            'maps_link': maps_link,
            'created_at': instance.created_at.strftime('%d.%m.%Y %H:%M:%S')
        }
        
        html_content = render_to_string('emails/emergency_alert_email.html', context)
        text_content = strip_tags(html_content)
        
        try:
            # Gönderen: Sistem (settings.DEFAULT_FROM_EMAIL)
            # Alıcı: Biz (settings.EMAIL_HOST_USER) - Kendimize mail atıyoruz
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.EMAIL_HOST_USER]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            print(f"Acil durum HTML maili gönderildi: {user.email}")
        except Exception as e:
            print(f"Acil durum maili gönderilemedi: {e}")
