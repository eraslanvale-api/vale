from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from orders.models import Order
from services.models import Service
from decimal import Decimal
from django.utils import timezone

User = get_user_model()

class DashboardAPITests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            role='Yönetici'
        )
        self.client.force_authenticate(user=self.admin_user)
        
        self.service = Service.objects.create(
            name='Test Service',
            slug='test-service',
            base_fee=Decimal('100.00'),
            per_km=Decimal('10.00')
        )
        
        self.order = Order.objects.create(
            user=self.admin_user,
            service=self.service,
            pickup_address='Pickup',
            dropoff_address='Dropoff',
            pickup_time=timezone.now(),
            price=Decimal('150.00'),
            distance_km=5.0,
            pickup_lat=41.0,
            pickup_lng=29.0,
            dropoff_lat=41.1,
            dropoff_lng=29.1
        )

    def test_dashboard_stats(self):
        url = reverse('dashboard_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_reservations'], 1)

    def test_waiting_reservations(self):
        url = reverse('waiting_reservations_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Order doesn't have a driver, so it should be in waiting list
        self.assertEqual(len(response.data), 1)

    def test_order_viewset(self):
        url = reverse('dashboard_orders-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_bulk_notification(self):
        url = reverse('bulk_notification_send')
        data = {
            'title': 'Test Bulk',
            'message': 'Hello all',
            'channels': ['email'],
            'group': 'all'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
