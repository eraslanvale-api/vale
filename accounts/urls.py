from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    SetNewPasswordView,
    PushTokenView,
    ExpoPushTokenView,
    VerifyAccountView,
    ResendVerificationView,
    DeleteAccountView,
    MembershipCancelView,
    AddressListCreateView,
    AddressDetailView,
    InvoiceListCreateView,
    InvoiceDetailView,
    EmergencyContactListCreateView,
    EmergencyContactDetailView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', ProfileView.as_view(), name='profile'),
    path('delete/', DeleteAccountView.as_view(), name='delete_account'),
    path('membership-cancel/', MembershipCancelView.as_view(), name='membership_cancel'),
    
    # Şifre sıfırlama işlemleri
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/verify/', PasswordResetVerifyView.as_view(), name='password_reset_verify'),
    path('password-reset/confirm/', SetNewPasswordView.as_view(), name='password_reset_confirm'),
    
    # Hesap doğrulama işlemleri
    path('verify-account/', VerifyAccountView.as_view(), name='verify_account'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend_verification'),
    
    # Push notification token
    path('push-token/', PushTokenView.as_view(), name='push_token'),
    path('expo-push-token/', ExpoPushTokenView.as_view(), name='expo_push_token'),
    
    # Adres işlemleri
    path('addresses/', AddressListCreateView.as_view(), name='address_list_create'),
    path('addresses/<uuid:pk>/', AddressDetailView.as_view(), name='address_detail'),

    # Fatura işlemleri
    path('invoices/', InvoiceListCreateView.as_view(), name='invoice_list_create'),
    path('invoices/<uuid:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),

    # Acil Durum Kişisi işlemleri
    path('emergency-contacts/', EmergencyContactListCreateView.as_view(), name='emergency_contact_list_create'),
    path('emergency-contacts/<uuid:pk>/', EmergencyContactDetailView.as_view(), name='emergency_contact_detail'),
]
