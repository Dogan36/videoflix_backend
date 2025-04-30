"""
users/models.py

Defines a custom user model using email as the unique identifier,
along with its manager and permissions mixin.
"""


from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings

class CustomUserManager(BaseUserManager):
    """
    Manager for CustomUser: handles creation of regular users and superusers.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a CustomUser with the given email and password.
        
        Args:
            email (str): The user's email address; used as the username.
            password (str): Raw password to hash and store.
            extra_fields: Additional model fields.
        
        Raises:
            ValueError: If no email is provided.
        """
        
        
        if not email:
            raise ValueError("E-Mail-Adresse ist erforderlich.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a superuser with all permissions.
        
        Ensures is_staff and is_superuser flags are set.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email instead of username,
    supports activation and staff flags.
    """
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        """
        Return the string representation of the user,
        which is their email address.
        """
        return self.email
    


