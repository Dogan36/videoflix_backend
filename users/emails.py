from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

def send_activation_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    activation_path = reverse("activate", kwargs={"uid": uid, "token": token})
    activation_url = f"{settings.FRONTEND_URL}{activation_path}"

    subject = "Activate your Videoflix account"

    # HTML + Fallback Text
    context = {"user": user, "activation_url": activation_url, "logo_url": f"{settings.FRONTEND_URL}/logo.png"}
    html_content = render_to_string("templates/activation_email.html", context)
    text_content = f"Hi {user.email},\nActivate here: {activation_url}"

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()