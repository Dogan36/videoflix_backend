"""
users/serializers.py

Serializers for user authentication: login and registration.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
from django.contrib.auth import get_user_model

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Validate email existence and password correctness.

        Steps:
        1) Check that a user with the given email exists.
        2) Verify the provided password matches the stored hash.
        Raises ValidationError on failure.
        Returns:
            attrs with 'user' key on success.
        """
        User = get_user_model()
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user with this email.")

        if not user.check_password(password):
            raise serializers.ValidationError("Wrong password.")

        attrs["user"] = user
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    """
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def create(self, validated_data):
        """
        Create a new CustomUser instance using the manager's create_user method.
        Ensures password hashing and any extra fields are handled.
        """
        return CustomUser.objects.create_user(**validated_data)