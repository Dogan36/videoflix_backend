from django.urls import path
from .views import RegisterView, ActivateAccountView, LoginView, ResendActivationView

app_name = "users"

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<int:uid>/<str:token>/', ActivateAccountView.as_view(), name='activate'),
    path("login/", LoginView.as_view(), name="login"),
    path("resend-activation/", ResendActivationView.as_view(), name="resend-activation"),
]