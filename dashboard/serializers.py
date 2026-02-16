from rest_framework import serializers
from orders.models import Order, OrderStop, EmergencyAlert, VehicleHandoverPhoto
from services.models import Service, Vehicle
from orders.serializers import OrderSerializer, OrderStopSerializer, VehicleHandoverPhotoSerializer
from accounts.models import User
from accounts.serializers import UserSerializer


class DashboardEmergencyAlertSerializer(serializers.ModelSerializer):
    """Dashboard için acil durum bildirim serializer'ı."""
    order_id = serializers.CharField(source='order.id', read_only=True)
    order_pickup = serializers.CharField(source='order.pickup_address', read_only=True)
    order_dropoff = serializers.CharField(source='order.dropoff_address', read_only=True)
    customer = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()
    
    class Meta:
        model = EmergencyAlert
        fields = [
            'id', 'order_id', 'order_pickup', 'order_dropoff',
            'customer', 'driver', 'lat', 'lng', 
            'created_at', 'is_resolved'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_customer(self, obj):
        user = obj.user
        if not user:
            return None
        return {
            'id': user.id,
            'full_name': user.full_name or f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
            'phone': user.phone_number
        }
    
    def get_driver(self, obj):
        driver = obj.order.driver if obj.order else None
        if not driver:
            return None
        return {
            'id': driver.id,
            'full_name': driver.full_name or f"{driver.first_name or ''} {driver.last_name or ''}".strip() or driver.email,
            'phone': driver.phone_number
        }


class DashboardOrderSerializer(OrderSerializer):
    userId = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True,
        required=False
    )

    def create(self, validated_data):
        stops_data = validated_data.pop('stops', [])
        order = Order.objects.create(**validated_data)
        for stop_data in stops_data:
            OrderStop.objects.create(order=order, **stop_data)
        return order

    def update(self, instance, validated_data):
        # Handle nested stops field
        stops_data = validated_data.pop('stops', None)
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update stops if provided
        if stops_data is not None:
            # Delete existing stops and create new ones
            instance.stops.all().delete()
            for stop_data in stops_data:
                OrderStop.objects.create(order=instance, **stop_data)
        
        return instance

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ['userId']


class DashboardUserSerializer(serializers.ModelSerializer):
    """
    Dashboard için kullanıcı yönetimi serializer'ı.
    Tüm kullanıcı bilgilerini yönetmek için.
    """
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'first_name', 'last_name',
            'phone_number', 'role', 'is_verified', 'is_active',
            'vehicle_plate', 'vehicle_model', 'date_joined', 'last_login',
            'password'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        
        # Email zorunlu değilse telefon numarasından üret
        email = validated_data.get('email')
        phone_number = validated_data.get('phone_number')
        
        if not email and phone_number:
            clean_phone = phone_number.replace(" ", "").replace("+", "")
            validated_data['email'] = f"{clean_phone}@noemail.vipvale.com"
        
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        
        # Full Name Fallback Logic
        full_name = ret.get('full_name')
        
        if not full_name and (instance.first_name or instance.last_name):
            full_name = f"{instance.first_name or ''} {instance.last_name or ''}".strip()
        
        if not full_name:
            email = instance.email
            if email and '@noemail.vipvale.com' not in email:
                full_name = email
            else:
                full_name = instance.phone_number
        
        ret['full_name'] = full_name
        return ret


class DashboardOrderPhotoGallerySerializer(serializers.ModelSerializer):
    """Sadece fotoğraflı siparişlerin galerisi için özet serializer."""
    photos = VehicleHandoverPhotoSerializer(many=True, source='handover_photos', read_only=True)
    customer_name = serializers.CharField(source='user.full_name', read_only=True)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'customer_name', 'driver_name', 'service_name', 
            'pickup_address', 'dropoff_address', 'pickup_time', 
            'photos', 'created_at'
        ]


class DashboardServiceSerializer(serializers.ModelSerializer):
    """Dashboard için servis yönetimi serializer'ı."""
    class Meta:
        model = Service
        fields = [
            'id', 'slug', 'name', 'is_active', 'image', 'description', 
            'base_fee', 'per_km', 'free_distance', 'show_price'
        ]


class DashboardVehicleSerializer(serializers.ModelSerializer):
    """Dashboard için araç yönetimi serializer'ı."""
    class Meta:
        model = Vehicle
        fields = [
            'id', 'plate', 'brand', 'model', 'color', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
