from rest_framework import serializers
from .models import Order, OrderStop
from services.serializers import ServiceSerializer
from services.models import Service
from accounts.models import Invoice
from accounts.serializers import UserSerializer

class OrderStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStop
        fields = ['address', 'lat', 'lng']

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

    pickupLoc = serializers.SerializerMethodField()
    dropoffLoc = serializers.SerializerMethodField()

    active = serializers.SerializerMethodField()
    dateLabel = serializers.SerializerMethodField()
    customerName = serializers.SerializerMethodField()
    statusLabel = serializers.CharField(source='get_status_display', read_only=True)
    time = serializers.SerializerMethodField()
    
    # Use UserSerializer for driver details
    driver = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'serviceId', 'serviceName', 'active', 'status', 'statusLabel',
            'pickup', 'dropoff', 'pickupTime', 'dateLabel', 'time',
            'price', 'paymentMethod', 'distanceKm', 'durationMin',
            'pickupLoc', 'dropoffLoc', 'stops',
            'pickupLat', 'pickupLng', 'dropoffLat', 'dropoffLng',
            'customerName', 'driver', 'created_at', 'invoiceId'
        ]
        read_only_fields = ['driver']

    def get_serviceName(self, obj):
        return obj.service.name if obj.service else None

    def get_customerName(self, obj):
        return obj.user.full_name if obj.user.full_name else obj.user.email

    def get_pickupLoc(self, obj):
        return {"lat": obj.pickup_lat, "lng": obj.pickup_lng}

    def get_dropoffLoc(self, obj):
        return {"lat": obj.dropoff_lat, "lng": obj.dropoff_lng}

    def get_active(self, obj):
        return obj.status == 'active'

    def get_dateLabel(self, obj):
        # Örn: 24 Kas 2025 formatı
        return obj.pickup_time.strftime("%d %b %Y") 

    def get_time(self, obj):
        return obj.pickup_time.strftime("%H:%M")
    
    def create(self, validated_data):
        stops_data = validated_data.pop('stops', [])
        service = validated_data.pop('service', None)
        
        # 'status' varsayılan olarak modelde 'scheduled' set ediliyor
        
        order = Order.objects.create(service=service, **validated_data)
        
        for i, stop_data in enumerate(stops_data):
            OrderStop.objects.create(order=order, order_index=i, **stop_data)
            
        return order
