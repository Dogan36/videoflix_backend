from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.serializers import ValidationError

from users.serializers import LoginSerializer, RegisterSerializer

User = get_user_model()

class LoginSerializerTest(TestCase):
    def setUp(self):
        self.password = "complexpass123"
        self.user = User.objects.create_user(
            email="test@example.com",
            password=self.password
        )

    def test_valid_credentials(self):
        data = {"email": self.user.email, "password": self.password}
        serializer = LoginSerializer(data=data, context={"request": None})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["user"], self.user)

    def test_nonexistent_email_raises_error(self):
        data = {"email": "nope@example.com", "password": "whatever"}
        serializer = LoginSerializer(data=data, context={"request": None})
        with self.assertRaises(ValidationError) as cm:
            serializer.is_valid(raise_exception=True)
        self.assertIn("No user with this email.", str(cm.exception))

    def test_wrong_password_raises_error(self):
        data = {"email": self.user.email, "password": "wrongpass"}
        serializer = LoginSerializer(data=data, context={"request": None})
        with self.assertRaises(ValidationError) as cm:
            serializer.is_valid(raise_exception=True)
        self.assertIn("Wrong password.", str(cm.exception))


class RegisterSerializerTest(TestCase):
    def test_create_user_with_valid_data(self):
        data = {"email": "new@example.com", "password": "secure123"}
        serializer = RegisterSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        # Benutzer existiert und Passwort gehashed
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        self.assertTrue(user.check_password("secure123"))

    def test_password_too_short(self):
        data = {"email": "short@example.com", "password": "123"}
        serializer = RegisterSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)