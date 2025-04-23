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
 

class RegisterView(APIView):
    def post(self, request):
        print(request.data)
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            if CustomUser.objects.filter(email=email).exists():
                return Response(
                    {"email": ["user with this email already exists."]},
                    status=status.HTTP_409_CONFLICT
                )        
            user = serializer.save()

            # Token erzeugen
            token = default_token_generator.make_token(user)
            uid = user.pk

            activation_url = request.build_absolute_uri(
                reverse("users:activate", kwargs={"uid": uid, "token": token})
            )

            # Mail senden
            send_activation_email(user)

            return Response({"detail": "Please check your email to verify your account."}, status=201)

        return Response(serializer.errors, status=400)
    
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
        print("✅ Login-View wurde aufgerufen")
        serializer = LoginSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # User ist inaktiv (nicht verifiziert)
            if not user.is_active:
                return Response(
                    {"detail": "Account not activated. Please verify your email."},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user_id": user.id,
                "email": user.email
            }, status=status.HTTP_200_OK)

        # Falls die E-Mail nicht gefunden wurde → 404
        email = request.data.get("email")
        if not CustomUser.objects.filter(email=email).exists():
            return Response(
                {"detail": "Email not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Allgemeiner Fehler (z. B. falsches Passwort)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


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
        print("CheckEmailExistsAPIView")
        email = request.data.get("email")
        print(email)
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(email=email).exists()
        return Response({"exists": exists}, status=status.HTTP_200_OK)
    
class RequestPasswordResetView(APIView):
    def post(self, request):
        email = request.data.get("email")
        print(email)
        if not email:
            return Response({"detail": "E-Mail-Adresse ist erforderlich."}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Kein Benutzer mit dieser E-Mail gefunden."}, status=404)
        send_password_reset_email(user)
        return Response({"detail": "E-Mail zum Zurücksetzen des Passworts wurde gesendet."}, status=200)
    

class ResetPasswordConfirmView(APIView):
    def post(self, request, uid, token):
        password = request.data.get("password")
        password2 = request.data.get("password2")

        if not password or not password2:
            return Response({"detail": "Beide Passwörter sind erforderlich."}, status=400)

        if password != password2:
            return Response({"detail": "Passwörter stimmen nicht überein."}, status=400)

        try:
            user = User.objects.get(pk=uid)
        except User.DoesNotExist:
            return Response({"detail": "Benutzer nicht gefunden."}, status=404)

        if not default_token_generator.check_token(user, token):
            return Response({"detail": "Token ist ungültig oder abgelaufen."}, status=400)

        user.set_password(password)
        user.save()
        return Response({"detail": "Passwort wurde erfolgreich geändert."}, status=200)


