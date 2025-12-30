from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags

def send_password_reset_email(email, code):
    subject = 'Premium Vale - Parola Sıfırlama Kodu'
    html_content = render_to_string('emails/password_reset_email.html', {'code': code})
    text_content = strip_tags(html_content)
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    try:
        msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Mail gönderme hatası: {e}")
        return False

def send_verification_email(email, code):
    subject = 'Premium Vale - Hesap Doğrulama Kodu'
    html_content = render_to_string('emails/verification_email.html', {'code': code})
    text_content = strip_tags(html_content)
    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    
    try:
        msg = EmailMultiAlternatives(subject, text_content, email_from, recipient_list)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        return True
    except Exception as e:
        print(f"Mail gönderme hatası: {e}")
        return False
