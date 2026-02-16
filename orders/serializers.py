from rest_framework import serializers
from .models import Order, OrderStop, EmergencyAlert, VehicleHandoverPhoto
from services.serializers import ServiceSerializer
from services.models import Service
from accounts.models import Invoice
from accounts.serializers import UserSerializer

class EmergencyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyAlert
        fields = ['id', 'order', 'lat', 'lng', 'created_at', 'is_resolved']
        read_only_fields = ['user', 'created_at', 'is_resolved']

class OrderStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStop
        fields = ['address', 'lat', 'lng']

class VehicleHandoverPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleHandoverPhoto
        fields = ['id', 'order', 'photo', 'photo_type', 'created_at']
        read_only_fields = ['created_at']
class OrderSerializer(serializers.ModelSerializer):
    stops = OrderStopSerializer(many=True, read_only=False, required=False)
    serviceId = serializers.SlugRelatedField(
        slug_field='slug', 
        queryset=Service.objects.all(), 
        source='service',
        write_only=True
    )
    invoiceId = serializers.PrimaryKeyRelatedField(
        queryset=Invoice.objects.all(),
        source='invoice',
        required=False,
        allow_null=True
    )
    serviceName = serializers.SerializerMethodField()
    
    # Input/Output fields mapping
    pickup = serializers.CharField(source='pickup_address')
    dropoff = serializers.CharField(source='dropoff_address')
    pickupTime = serializers.DateTimeField(source='pickup_time')
    paymentMethod = serializers.CharField(source='payment_method', required=False, allow_null=True)
    distanceKm = serializers.FloatField(source='distance_km')
    durationMin = serializers.IntegerField(source='duration_min')
    
    pickupLat = serializers.FloatField(source='pickup_lat')
    pickupLng = serializers.FloatField(source='pickup_lng')
    dropoffLat = serializers.FloatField(source='dropoff_lat')
    dropoffLng = serializers.FloatField(source='dropoff_lng')
    
    emergencyContactName = serializers.CharField(source='emergency_contact_name', required=False, allow_blank=True, allow_null=True)
    emergencyContactPhone = serializers.CharField(source='emergency_contact_phone', required=False, allow_blank=True, allow_null=True)

    pickupLoc = serializers.SerializerMethodField()
    dropoffLoc = serializers.SerializerMethodField()

    active = serializers.SerializerMethodField()
    dateLabel = serializers.SerializerMethodField()
    customerName = serializers.SerializerMethodField()
    statusLabel = serializers.CharField(source='get_status_display', read_only=True)
    time = serializers.SerializerMethodField()
    has_active_emergency = serializers.SerializerMethodField()
    show_price = serializers.SerializerMethodField()
    
    # Use UserSerializer for driver details
    driver = UserSerializer(read_only=True)
    
    vehicle_details = serializers.SerializerMethodField()
    
    handover_photos = VehicleHandoverPhotoSerializer(many=True, read_only=True)

    def get_serviceName(self, obj):
        return obj.service.name if obj.service else "Standart Hizmet"

    def get_pickupLoc(self, obj):
        return {
            "lat": obj.pickup_lat,
            "lng": obj.pickup_lng,
            "address": obj.pickup_address
        }

    def get_dropoffLoc(self, obj):
        return {
            "lat": obj.dropoff_lat,
            "lng": obj.dropoff_lng,
            "address": obj.dropoff_address
        }

    def get_active(self, obj):
        return obj.status in ['scheduled', 'searching', 'assigned', 'accepted', 'on_way', 'in_progress']

    def get_dateLabel(self, obj):
        return obj.pickup_time.strftime('%d.%m.%Y') if obj.pickup_time else ""

    def get_customerName(self, obj):
        # 1. Full Name
        if obj.user.full_name:
            return obj.user.full_name
            
        # 2. First + Last
        if obj.user.first_name or obj.user.last_name:
            return f"{obj.user.first_name} {obj.user.last_name}"
            
        # 3. Email (if not dummy)
        email = obj.user.email
        if email and '@noemail.vipvale.com' not in email:
            return email
            
        # 4. Phone
        return obj.user.phone_number

    def get_time(self, obj):
        return obj.pickup_time.strftime('%H:%M') if obj.pickup_time else ""

    def get_has_active_emergency(self, obj):
        return obj.emergency_alerts.filter(is_resolved=False).exists()

    def get_show_price(self, obj):
        return obj.service.show_price if obj.service else True

    def get_vehicle_details(self, obj):
        if obj.vehicle:
            return {
                "plate": obj.vehicle.plate,
                "brand": obj.vehicle.brand,
                "model": obj.vehicle.model,
                "color": getattr(obj.vehicle, 'color', '')
            }
        return {
            "plate": obj.license_plate or "Plaka Yok",
            "brand": "",
            "model": "Araç bilgisi yok",
            "color": ""
        }

    def create(self, validated_data):
        # Handle writable nested 'stops'
        stops_data = validated_data.pop('stops', [])
        
        # Create the Order instance
        order = super().create(validated_data)
        
        # Create the OrderStop instances
        for i, stop_data in enumerate(stops_data):
            OrderStop.objects.create(order=order, order_index=i, **stop_data)
            
        return order

    class Meta:
        model = Order
        fields = [
            'id', 'serviceId', 'serviceName', 'active', 'status', 'statusLabel',
            'pickup', 'dropoff', 'pickupTime', 'dateLabel', 'time',
            'price', 'paymentMethod', 'distanceKm', 'durationMin',
            'pickupLoc', 'dropoffLoc', 'stops',
            'pickupLat', 'pickupLng', 'dropoffLat', 'dropoffLng',
            'emergencyContactName', 'emergencyContactPhone',
            'customerName', 'driver', 'created_at', 'invoiceId',
            'license_plate', 'vehicle_details', 'has_active_emergency',
            'handover_photos', 'show_price'
        ]
        read_only_fields = ['driver']