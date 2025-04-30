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
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # ... E-Mail versenden, Response wie gehabt ...
            send_activation_email(user)
            return Response(
                {"detail": "Please check your email to verify your account."},
                status=status.HTTP_201_CREATED,
            )

        # Immer nur eine allgemeine Fehlermeldung
        return Response(
            {"detail": "Registration failed. Please check your input."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ActivateAccountView(APIView):
    def get(self, request, uid, token):
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
    def post(self, request):
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
    def post(self, request):
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
    # 1) Base64 → bytes
    uid_bytes = urlsafe_base64_decode(uidb64)
    # 2) bytes → str
    uid_str = force_str(uid_bytes)
    # 3) str → int (Primary Key)
    return int(uid_str)


class ResetPasswordConfirmView(APIView):
    def post(self, request, uid, token):
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
