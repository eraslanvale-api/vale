from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class AccountsAPITests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')
        self.user_data = {
            'email': 'testuser@example.com',
            'password': 'password123',
            'full_name': 'Test User',
            'phone_number': '5551234567'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.user.is_verified = True
        self.user.save()

    def test_register_user(self):
        data = {
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'full_name': 'New User',
            'phone_number': '5557654321'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(email='newuser@example.com').count(), 1)

    def test_login_user(self):
        data = {
            'email': 'testuser@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if login returns a token (based on typical DRF JWT or Token auth)
        self.assertIn('token', response.data)

    def test_get_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_address_management(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('address_list_create')
        
        # Create address
        data = {'title': 'Home', 'description': 'Main residence', 'lat': 41.0, 'lng': 29.0}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        address_id = response.data['id']
        
        # List addresses
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
        
        # Update address
        detail_url = reverse('address_detail', kwargs={'pk': address_id})
        response = self.client.patch(detail_url, {'title': 'Work'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Work')

    def test_invoice_management(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('invoice_list_create')
        
        # Create invoice
        data = {'full_name': 'Test Invoice', 'invoice_type': 'Bireysel', 'city': 'Istanbul'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invoice_id = response.data['id']
        
        # List invoices
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)

    def test_emergency_contact_management(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('emergency_contact_list_create')
        
        # Create contact
        data = {'name': 'Emergency Contact', 'phone_number': '123456', 'relationship': 'Friend'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        contact_id = response.data['id']
        
        # Get list
        response = self.client.get(url)
        self.assertEqual(len(response.data), 1)
