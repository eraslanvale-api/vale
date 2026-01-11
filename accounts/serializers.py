from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, PushToken, ExpoPushToken, Address, Invoice, EmergencyContact

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('id','email', 'password', 'full_name', 'phone_number','role','is_verified')
        
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def validate_phone_number(self, value):
        """Telefon numarası benzersiz olmalı"""
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Bu telefon numarası ile kayıtlı bir kullanıcı zaten mevcut.")
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','email', 'full_name',  'phone_number', 'role','is_verified', 'vehicle_plate', 'vehicle_model')
        read_only_fields = ('id', 'email', 'is_staff', 'is_superuser')


    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if not ret.get('full_name') and (instance.first_name or instance.last_name):
             ret['full_name'] = f"{instance.first_name or ''} {instance.last_name or ''}".strip()
        return ret

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("Email veya parola hatalı")
        else:
             raise serializers.ValidationError("Email ve parola gereklidir")
             
        attrs['user'] = user
        return attrs

class PasswordResetRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)

class PasswordResetVerifySerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=4)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        code = attrs.get('code')
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError('Bu telefon numarası ile kayıtlı bir kullanıcı bulunamadı.')

        if user.password_reset_code != code:
            raise serializers.ValidationError('Girdiğiniz kod hatalı. Lütfen tekrar deneyiniz.')

        if user.password_reset_code_expired:
            raise serializers.ValidationError('Bu kodun süresi dolmuş. Lütfen yeni bir kod isteyiniz.')

        return attrs

class SetNewPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=4)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        code = attrs.get('code')
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError('Bu telefon numarası ile kayıtlı bir kullanıcı bulunamadı.')
        
        if user.password_reset_code != code:
            raise serializers.ValidationError('Girdiğiniz kod hatalı veya süresi dolmuş.')
            
        if user.password_reset_code_expired:
            raise serializers.ValidationError('Bu kodun süresi dolmuş. Lütfen yeni bir kod isteyiniz.')
        
        attrs['user'] = user
        return attrs

class PushTokenSerializer(serializers.ModelSerializer):
    platform = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = PushToken
        fields = ('token', 'platform')
        extra_kwargs = {
            'token': {'validators': []}
        }

    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data['token']
        platform = validated_data.get('platform', 'unknown')
        
        # Check if token already exists
        existing_token = PushToken.objects.filter(token=token).first()
        
        if existing_token:
            # Token exists - update user association if different
            # ALWAYS return the existing token instance to avoid validation errors in unique constraints
            if existing_token.user != user:
                existing_token.user = user
                existing_token.platform = platform
                existing_token.save()
            elif existing_token.platform != platform:
                # Same user but platform changed
                existing_token.platform = platform
                existing_token.save()
            return existing_token
        else:
            # New token - optionally remove old tokens for this user on same platform
            if platform:
                PushToken.objects.filter(user=user, platform=platform).delete()
            
            # Create new token
            push_token = PushToken.objects.create(
                user=user,
                token=token,
                platform=platform
            )
            return push_token

class ExpoPushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpoPushToken
        fields = ('token',)
        extra_kwargs = {
            'token': {'validators': []}
        }

    def create(self, validated_data):
        user = self.context['request'].user
        token = validated_data['token']
        
        # Check if token already exists
        existing_token = ExpoPushToken.objects.filter(token=token).first()
        
        if existing_token:
            # Token exists - update user association if different
            if existing_token.user != user:
                existing_token.user = user
                existing_token.save()
            return existing_token
        else:
            # Remove old tokens for this user
            ExpoPushToken.objects.filter(user=user).delete()
            
            # Create new token
            push_token = ExpoPushToken.objects.create(
                user=user,
                token=token
            )
            return push_token


class AddressSerializer(serializers.ModelSerializer):
    is_default = serializers.BooleanField(default=False)
    
    class Meta:
        model = Address
        fields = ('id', 'title', 'description', 'lat', 'lng', 'is_default')
        read_only_fields = ('id',)


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ('id', 'email', 'invoice_type', 'full_name', 'company_name', 'tax_number', 'tax_office', 'citizen_id', 'phone_number', 'postal_code', 'city', 'district', 'description', 'is_default')
        read_only_fields = ('id',)



class AccountVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)
    code = serializers.CharField(required=True, max_length=4)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        code = attrs.get('code')
        
        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError('Kullanıcı bulunamadı.')

        if user.is_verified:
            raise serializers.ValidationError('Hesap zaten doğrulanmış.')

        if user.verification_code != code:
            raise serializers.ValidationError('Doğrulama kodu hatalı.')

        if user.verification_code_expired:
            raise serializers.ValidationError('Kodun süresi dolmuş. Lütfen yeni kod isteyiniz.')
            
        attrs['user'] = user
        return attrs

class ResendVerificationSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=True)


class EmergencyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyContact
        fields = ('id', 'name', 'phone_number', 'relationship')
        read_only_fields = ('id',)


class PasswordChangeRequestSerializer(serializers.Serializer):
    """Şifre değiştirme isteği için mevcut şifreyi doğrular"""
    current_password = serializers.CharField(required=True, write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Mevcut şifreniz hatalı.')
        return value


class PasswordChangeConfirmSerializer(serializers.Serializer):
    """SMS kodu ve yeni şifre ile şifre değişikliğini tamamlar"""
    code = serializers.CharField(required=True, max_length=4)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)

    def validate(self, attrs):
        user = self.context['request'].user
        code = attrs.get('code')

        if user.password_reset_code != code:
            raise serializers.ValidationError({'code': 'Doğrulama kodu hatalı.'})

        if user.password_reset_code_expired:
            raise serializers.ValidationError({'code': 'Kodun süresi dolmuş. Lütfen yeni kod isteyiniz.'})

        return attrs
