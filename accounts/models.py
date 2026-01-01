import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

import os
from datetime import datetime, timedelta
import secrets
from django.conf import settings


class CustomUserManager(BaseUserManager):
    """
    Email ile kullanıcı oluşturmak için Custom User Manager
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email adresi zorunludur')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Password reset
    password_reset_code = models.CharField(max_length=4, null=True, blank=True)
    password_reset_code_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Account verification
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=4, null=True, blank=True)
    verification_code_sent_at = models.DateTimeField(null=True, blank=True)

    role = models.CharField(max_length=20, choices=[('Kullanıcı', 'Kullanıcı'), ('Şoför', 'Şoför')], default='Kullanıcı')
    
    # Driver specific fields
    vehicle_plate = models.CharField(max_length=20, blank=True, null=True)
    vehicle_model = models.CharField(max_length=100, blank=True, null=True)
    
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    @property
    def password_reset_code_expired(self):
        if not self.password_reset_code_sent_at:
            return False
        expiration_time = self.password_reset_code_sent_at + timedelta(
            hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24)
        )
        return timezone.now() > expiration_time

    def generate_password_reset_code(self):
        """4 haneli kriptografik olarak güvenli rastgele kod oluştur ve kaydet"""
        code = f"{secrets.randbelow(10000):04d}"
        self.password_reset_code = code
        self.password_reset_code_sent_at = timezone.now()
        self.save(update_fields=['password_reset_code', 'password_reset_code_sent_at'])
        return code

    @property
    def verification_code_expired(self):
        if not self.verification_code_sent_at:
            return False
        expiration_time = self.verification_code_sent_at + timedelta(
            hours=getattr(settings, 'VERIFICATION_CODE_EXPIRY_HOURS', 24)
        )
        return timezone.now() > expiration_time

    def generate_verification_code(self):
        """4 haneli hesap doğrulama kodu oluştur"""
        code = f"{secrets.randbelow(10000):04d}"
        self.verification_code = code
        self.verification_code_sent_at = timezone.now()
        self.save(update_fields=['verification_code', 'verification_code_sent_at'])
        return code


class PushToken(models.Model):
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=20, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{(self.user and getattr(self.user, 'email', None)) or 'admin'} - {self.platform or 'unknown'} - {self.token[:12]}..."

class ExpoPushToken(models.Model):
    token = models.CharField(max_length=512, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expo_push_tokens")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.token[:15]}..."


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="addresses")
    title = models.CharField(max_length=255,blank=True,null=True)
    description = models.CharField(max_length=255,blank=True,null=True)
    lat = models.FloatField(blank=True,null=True)
    lng = models.FloatField(blank=True,null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.title} - {self.description}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
    related_name="invoices")
    email = models.EmailField(max_length=255, blank=True,null=True)
    invoice_type = models.CharField(max_length=20, choices=[('Bireysel', 'Bireysel'), ('Kurumsal', 'Kurumsal')], default='Bireysel')
    full_name = models.CharField(max_length=255, blank=True,null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    tax_office = models.CharField(max_length=255, blank=True, null=True)
    citizen_id = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True,null=True)
    postal_code = models.CharField(max_length=10, blank=True,null=True)
    city = models.CharField(max_length=255, blank=True,null=True)
    district = models.CharField(max_length=255, blank=True,null=True)
    description = models.CharField(max_length=255,blank=True,null=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.email} - {self.invoice_type} - {self.full_name} - {self.email} - {self.phone_number} - {self.postal_code} - {self.city} - {self.district} - {self.description}"
    def save(self, *args, **kwargs):
        if self.is_default:
            Invoice.objects.filter(user=self.user).update(is_default=False)
        super().save(*args, **kwargs)


class EmergencyContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="emergency_contacts")
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    relationship = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.name} - {self.phone_number}"