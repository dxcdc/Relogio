from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from datetime import timedelta
import json
from core.axes_handlers import lockout_response

class AxesLockoutTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_lockout_response_redirect(self):
        request = self.factory.post('/login/', {'username': 'testuser'})
        response = lockout_response(request, credentials={'username': 'testuser'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/?locked=1&time='))

    def test_lockout_response_api(self):
        request = self.factory.post('/api/login/', {'username': 'testuser'})
        response = lockout_response(request, credentials={'username': 'testuser'})
        self.assertEqual(response.status_code, 429)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIn('Muitas tentativas inválidas', data['detail'])

    @override_settings(AXES_COOLOFF_TIME=0.5)
    def test_lockout_response_numeric_cooloff(self):
        request = self.factory.post('/login/', {'username': 'testuser'})
        response = lockout_response(request, credentials={'username': 'testuser'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/?locked=1&time='))
