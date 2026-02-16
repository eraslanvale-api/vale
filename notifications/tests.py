from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Notification
import uuid

User = get_user_model()

class NotificationsAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='notify@example.com',
            password='password123'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Hello world'
        )
        self.list_url = reverse('notification_list')

    def test_list_notifications(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_notification_detail(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('notification_detail', kwargs={'id': self.notification.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Notification')

    def test_mark_all_read(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('mark_all_read')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
