from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import RegisterSerializer, LoginSerializer
from .models import CustomUser 
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .emails import send_activation_email


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
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
            user = CustomUser.objects.get(pk=uid)
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
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user_id": user.id,
                "email": user.email
            })
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

