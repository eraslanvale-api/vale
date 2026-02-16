from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import ConfigModel

class ConfigAPITests(APITestCase):
    def setUp(self):
        self.config = ConfigModel.objects.create(
            termsUrl='http://example.com/terms'
        )
        self.config_url = reverse('get_config')

    def test_get_config(self):
        response = self.client.get(self.config_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # response returns a list of configs if multiple, or a single one based on view logic
        # Usually it returns the latest or only one.
        if isinstance(response.data, list):
             self.assertGreaterEqual(len(response.data), 1)
        else:
             self.assertEqual(response.data['termsUrl'], 'http://example.com/terms')
