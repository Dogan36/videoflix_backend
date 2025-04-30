"""
users/views.py

API endpoints for user registration, activation, login, and password management.
"""

from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework.views import APIView, View
from rest_framework.response import Response
from .serializers import RegisterSerializer, LoginSerializer
from .models import CustomUser
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .emails import send_activation_email, send_password_reset_email
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str


class RegisterView(APIView):
    """
    POST /users/register/
    Creates a new user and sends an activation email.
    Returns a generic success or failure message for security.
    """
    def post(self, request):
        """
        Validate incoming data with RegisterSerializer.
        On success: save user, send activation email, return 201.
        On failure: return 400 with a generic error detail.
        """
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            send_activation_email(user)
            return Response(
                {"detail": "Please check your email to verify your account."},
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"detail": "Registration failed. Please check your input."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ActivateAccountView(APIView):
    """
    GET /users/activate/<uid>/<token>/
    Verifies the activation token and activates the user account.
    """
    def get(self, request, uid, token):
        """
        Decode UID, fetch user, check token.
        On success: mark user active.
        On failure: return 400 with generic error detail.
        """
        try:
            uid_decoded = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid_decoded)
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid user"}, status=400)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({"detail": "Account verified!"}, status=200)
        else:
            return Response({"error": "Invalid or expired token"}, status=400)


class LoginView(APIView):
    """
    POST /users/login/
    Authenticates a user and returns an auth token.
    """
    def post(self, request):
        """
        Validate credentials via LoginSerializer.
        Check is_active flag.
        On success: return token and user info.
        On failure: return 400 or 401 with generic detail.
        """
        serializer = LoginSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            if not user.is_active:
                return Response(
                    {"detail": "Account not activated. Please verify your email."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {"token": token.key, "user_id": user.id, "email": user.email},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"detail": "Invalid email or password."}, status=status.HTTP_400_BAD_REQUEST
        )


class ResendActivationView(APIView):
    """
    POST /users/resend-activation/
    Resends the account activation email if the user exists and is inactive.
    Always returns 200 with a generic message.
    """
    def post(self, request):
        """
        Extract email, attempt lookup.
        If found & inactive: send activation email.
        Otherwise: no-op for security.
        """
        email = request.data.get("email")
        if not email:
            return Response({"detail": "Email is required."}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
            if user.is_active:
                return Response({"detail": "Account already activated."}, status=400)

            send_activation_email(user)
            return Response({"detail": "Activation email resent."})

        except ObjectDoesNotExist:
            # Gib trotzdem dieselbe Antwort aus Sicherheitsgründen
            return Response({"detail": "Activation email resent."})


User = get_user_model()


class CheckEmailExistsAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response(
                {"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        exists = User.objects.filter(email=email).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)


class RequestPasswordResetView(APIView):
    """
    POST /users/password-reset/
    Initiates password reset by sending an email if the account exists.
    Always responds with 200 and a generic detail.
    """
    def post(self, request):
        email = request.data.get("email")
        if email:
            try:
                user = User.objects.get(email=email)
                send_password_reset_email(user)
            except User.DoesNotExist:
                pass
        # Immer dieselbe Positive-Response
        return Response(
            {
                "detail": "If an account with that email exists, you will receive a reset link."
            },
            status=status.HTTP_200_OK,
        )


def decode_uid(uidb64):
    """
    Helper to decode URL-safe base64 UID into integer PK.
    """
    uid_bytes = urlsafe_base64_decode(uidb64)
    uid_str = force_str(uid_bytes)
    return int(uid_str)


class ResetPasswordConfirmView(APIView):
    """
    POST /users/password-reset-confirm/<uid>/<token>/
    Validates new password and token, updates the user's password.
    Returns generic success or failure messages.
    """
    def post(self, request, uid, token):
        """
        1) Verify that passwords match.
        2) Decode UID and fetch user.
        3) Check token validity.
        4) Set new password and save.
        5) Return 200 on success or 400 on failure.
        """
        password  = request.data.get("password")
        password2 = request.data.get("password2")

        if not password or password != password2:
            return Response(
                {"detail": "Password reset failed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pk   = decode_uid(uid)
            user = CustomUser.objects.get(pk=pk)
        except (ValueError, CustomUser.DoesNotExist):
            return Response(
                {"detail": "Password reset failed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Password reset failed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(password)
        user.save()
        return Response({"detail": "Password has been reset."}, status=status.HTTP_200_OK)
