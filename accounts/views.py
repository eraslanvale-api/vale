from rest_framework import status, generics, permissions, views
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import logout
from .models import User, PushToken, Address, Invoice, EmergencyContact
from .utils import send_password_reset_email, send_verification_email

from .serializers import (
    UserCreateSerializer, 
    UserSerializer, 
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer, 
    SetNewPasswordSerializer, 
    PushTokenSerializer,
    ExpoPushTokenSerializer,
    AddressSerializer,
    InvoiceSerializer,
    AccountVerificationSerializer,
    ResendVerificationSerializer,
    EmergencyContactSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        # Kayıt sonrası doğrulama kodu gönder
        code = user.generate_verification_code()
        send_verification_email(user.email, code)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Hesap doğrulanmamışsa uyarı dön veya izin verme
            # if not user.is_verified:
            #     return Response({"error": "Hesabınızı doğrulamanız gerekmektedir."}, status=status.HTTP_403_FORBIDDEN)
            
            token, created = Token.objects.get_or_create(user=user)
            
            # Profil doluluk oranı veya diğer bilgiler eklenebilir
            # Dönüş formatı: ["0", "Mesaj", "Token", "Role"]
            return Response({                
                "token":token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        logout(request)
        return Response({"message": "Çıkış yapıldı"}, status=status.HTTP_200_OK)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

class PasswordResetRequestView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                code = user.generate_password_reset_code()
                send_password_reset_email(user.email, code)
                return Response({"message": "Sıfırlama kodu gönderildi"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # Güvenlik için kullanıcı bulunamadı demeyebiliriz, ama UX için şimdilik diyelim
                return Response({"error": "Kullanıcı bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetVerifyView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Kod doğrulandı"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SetNewPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['new_password']
            user.set_password(new_password)
            user.password_reset_code = None # Kodu geçersiz kıl
            user.save()
            return Response({"message": "Parola başarıyla güncellendi"}, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PushTokenView(generics.CreateAPIView):
    serializer_class = PushTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

class ExpoPushTokenView(generics.CreateAPIView):
    serializer_class = ExpoPushTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

class VerifyAccountView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = AccountVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            user.is_verified = True
            user.verification_code = None
            user.save()
            
            # Otomatik giriş için token oluşturabiliriz
            token, _ = Token.objects.get_or_create(user=user)
            
            return Response({
                "message": "Hesap başarıyla doğrulandı",
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                if user.is_verified:
                    return Response({"message": "Hesap zaten doğrulanmış"}, status=status.HTTP_200_OK)
                
                code = user.generate_verification_code()
                send_verification_email(user.email, code)
                return Response({"message": "Doğrulama kodu tekrar gönderildi"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "Kullanıcı bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        # Hesabı tamamen silmek yerine pasife alıyoruz (Soft Delete)
        user.is_active = False
        user.save()
        
        # Token'ı silerek oturumu sonlandır
        try:
            user.auth_token.delete()
        except:
            pass
            
        return Response({"message": "Hesabınız başarıyla kapatıldı."}, status=status.HTTP_200_OK)

class MembershipCancelView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        # Üyelik iptali mantığı (örneğin hesabı pasife alma)
        user.is_active = False
        user.save()
        # Token'ı silerek oturumu sonlandır
        try:
            user.auth_token.delete()
        except:
            pass
        return Response({"message": "Üyeliğiniz iptal edildi."}, status=status.HTTP_200_OK)

class AddressListCreateView(generics.ListCreateAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        # Eğer kullanıcının hiç adresi yoksa, ilk eklenen adres varsayılan olsun
        if not Address.objects.filter(user=user).exists():
            serializer.save(user=user, is_default=True)
        else:
            serializer.save(user=user)

class InvoiceListCreateView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user = self.request.user
        # Eğer kullanıcının hiç faturası yoksa, ilk eklenen fatura varsayılan olsun
        if not Invoice.objects.filter(user=user).exists():
            serializer.save(user=user, is_default=True)
        else:
            serializer.save(user=user)

class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)

class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class EmergencyContactListCreateView(generics.ListCreateAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EmergencyContactDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmergencyContact.objects.filter(user=self.request.user)
