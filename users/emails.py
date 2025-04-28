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
    activation_path = reverse("users:activate", kwargs={"uid": uid, "token": token})
    activation_url = f"{settings.FRONTEND_URL}{activation_path}"
    subject = "Activate your Videoflix account"

    # HTML + Fallback Text
    context = {"user": user, "activation_url": activation_url, "logo_url": f"{settings.FRONTEND_URL}/logo.png"}
    html_content = render_to_string("activation_email.html", context)
    text_content = f"Hi {user.email},\nActivate here: {activation_url}"

    msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    
def send_password_reset_email(user):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"


    subject = "Reset your Videoflix password"
    context = {
        "user": user,
        "reset_url": reset_url,
        "logo_url": f"{settings.FRONTEND_URL}/logo.png",
    }

    # 5. HTML‑Versions und Plain‑Text‑Fallback rendern
    html_content = render_to_string("password_reset_email.html", context)
    text_content = (
        f"Hi {user.email},\n\n"
        f"You requested a password reset for your Videoflix account.\n"
        f"Please click the link below to set a new password:\n\n"
        f"{reset_url}\n\n"
        "If you didn't request this, just ignore this email."
    )


    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()