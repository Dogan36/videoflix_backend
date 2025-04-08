from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)

            if not user:
                raise serializers.ValidationError("Invalid credentials.")

            if not user.is_active:
                raise serializers.ValidationError("Account is not active. Please verify your email.")

            attrs["user"] = user
            return attrs

        raise serializers.ValidationError("Must include email and password.")

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)