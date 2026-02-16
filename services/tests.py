from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Service
from decimal import Decimal

class ServicesAPITests(APITestCase):
    def setUp(self):
        self.service = Service.objects.create(
            name='Standard Service',
            slug='standard-service',
            base_fee=Decimal('50.00'),
            per_km=Decimal('5.00')
        )
        self.list_url = reverse('service_list')

    def test_list_services(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response data contains the service
        self.assertTrue(len(response.data) >= 1)

    def test_service_detail_by_id(self):
        url = reverse('service_detail', kwargs={'id': self.service.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Standard Service')

    def test_service_detail_by_slug(self):
        url = reverse('service_detail_by_slug', kwargs={'slug': 'standard-service'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Standard Service')
