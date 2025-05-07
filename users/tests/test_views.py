from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserViewsTest(APITestCase):
    def setUp(self):
        self.register_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.activate_url_name = 'users:activate'
        self.resend_activation_url = reverse('users:resend-activation')
        self.request_reset_url = reverse('users:password-reset')
        self.reset_confirm_url_name = 'users:password-reset-confirm'
        self.user_email = 'test@example.com'
        self.user_password = 'password123'
        self.user = User.objects.create_user(email=self.user_email, password=self.user_password, is_active=False)

    def test_register_success(self):
        data = {'email': 'newuser@example.com', 'password': 'securepass'}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(email='dup@example.com', password='abc123')
        data = {'email': 'dup@example.com', 'password': 'xyz789'}
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_inactive_user(self):
        data = {'email': self.user_email, 'password': self.user_password}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_success(self):
        self.user.is_active = True
        self.user.save()
        data = {'email': self.user_email, 'password': self.user_password}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_activate_account_success(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse(self.activate_url_name, kwargs={'uid': uid, 'token': token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_activate_account_invalid(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid_token = 'wrong-token'
        url = reverse(self.activate_url_name, kwargs={'uid': uid, 'token': invalid_token})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_activation(self):
        url = self.resend_activation_url
        response = self.client.post(url, {'email': self.user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_password_reset_success(self):
        self.user.is_active = True
        self.user.save()
        url = self.request_reset_url
        response = self.client.post(url, {'email': self.user_email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_request_password_reset_not_found(self):
        url = self.request_reset_url
        response = self.client.post(url, {'email': 'noone@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_password_confirm_success(self):
        self.user.is_active = True
        self.user.save()
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse(self.reset_confirm_url_name, kwargs={'uid': uid, 'token': token})
        data = {'password': 'newpass123', 'password2': 'newpass123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_reset_password_confirm_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        url = reverse(self.reset_confirm_url_name, kwargs={'uid': uid, 'token': 'bad'})
        data = {'password': 'newpass123', 'password2': 'newpass123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_confirm_mismatch(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse(self.reset_confirm_url_name, kwargs={'uid': uid, 'token': token})
        data = {'password': 'pass1', 'password2': 'pass2'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
