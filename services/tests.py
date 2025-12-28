from django.test import TestCase

# Create your tests here.
from django.core.mail import send_mail

send_mail(
    subject='Django Test Mail',
    message='Bu mail Django SMTP üzerinden gönderildi.',
    from_email=None,  # DEFAULT_FROM_EMAIL kullanılır
    recipient_list=['teknoktay@gmail.com'],
    fail_silently=False,
)
