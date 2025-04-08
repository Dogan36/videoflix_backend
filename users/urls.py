
from django.urls import path
from .views import RegisterView, ActivateAccountView, LoginView, ResendActivationView, CheckEmailExistsAPIView, ResetPasswordConfirmView, RequestPasswordResetView




app_name = "users"

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<str:uid>/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name="login"),
    path('resend-activation/', ResendActivationView.as_view(), name="resend-activation"),
    path('check-email/', CheckEmailExistsAPIView.as_view(), name="check-email"),
    path('password-reset/', RequestPasswordResetView.as_view(), name="password-reset"),
    path('password-reset-confirm/<str:uid>/<str:token>/', ResetPasswordConfirmView.as_view(), name="password-reset-confirm"),
]