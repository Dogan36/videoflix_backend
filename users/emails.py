from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator


def send_activation_email(user):
    """
    Sends an activation email to the user with a unique token link.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    activation_path = reverse("users:activate", kwargs={"uid": uid, "token": token})
    activation_url = f"{settings.FRONTEND_URL}{activation_path}"

    context = {
        "user": user,
        "activation_url": activation_url,
        "logo_url": "https://videoflix.dogan-celik.com/logo_full.png"
    }
    subject = "Activate your Videoflix account"
    text_content = f"Hi {user.email},\nActivate here: {activation_url}"

    _send_email(
        subject=subject,
        to_email=user.email,
        template_name="activation_email.html",
        context=context,
        text_content=text_content
    )


def send_password_reset_email(user):
    """
    Sends a password reset email to the user with a unique token link.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

    context = {
        "user": user,
        "reset_url": reset_url,
        "logo_url": "https://videoflix.dogan-celik.com/logo_full.png",
    }
    subject = "Reset your Videoflix password"
    text_content = (
        f"Hi {user.email},\n\n"
        f"You requested a password reset for your Videoflix account.\n"
        f"Please click the link below to set a new password:\n\n"
        f"{reset_url}\n\n"
        "If you didn't request this, just ignore this email."
    )

    _send_email(
        subject=subject,
        to_email=user.email,
        template_name="password_reset_email.html",
        context=context,
        text_content=text_content
    )


def _send_email(subject, to_email, template_name, context, text_content):
    """
    Renders and sends an HTML + text fallback email.
    """
    html_content = render_to_string(template_name, context)
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()
