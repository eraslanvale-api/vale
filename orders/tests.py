from django.test import TestCase
from django.contrib.auth import get_user_model
from orders.serializers import OrderSerializer
from orders.models import Order
from services.models import Service
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class OrderSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            phone_number='5551234567',
            role='Müşteri'
        )
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            base_fee=Decimal('100.00'),
            per_km=Decimal('10.00')
        )

    def test_create_order_with_stops(self):
        data = {
            'serviceId': 'test-service',
            'pickup': 'Pickup Address',
            'dropoff': 'Dropoff Address',
            'pickupTime': timezone.now().isoformat(),
            'price': '150.00',
            'distanceKm': 5.0,
            'durationMin': 15,
            'pickupLat': 41.0,
            'pickupLng': 29.0,
            'dropoffLat': 41.1,
            'dropoffLng': 29.1,
            'stops': [
                {'address': 'Stop 1', 'lat': 41.05, 'lng': 29.05},
                {'address': 'Stop 2', 'lat': 41.08, 'lng': 29.08}
            ]
        }
        
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        
        order = serializer.save(user=self.user)
        
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.stops.count(), 2)
        self.assertEqual(order.stops.first().address, 'Stop 1')
        self.assertEqual(order.stops.last().address, 'Stop 2')
