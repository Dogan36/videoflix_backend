from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser
from django.contrib.auth import get_user_model
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        User = get_user_model()
        email = attrs.get("email")
        password = attrs.get("password")

        # 1) Existenz prüfen
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user with this email.")


        # 3) Passwort prüfen (ohne is_active-Check)
        if not user.check_password(password):
            raise serializers.ValidationError("Wrong password.")

        # 4) Alles gut
        attrs["user"] = user
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'password']

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)