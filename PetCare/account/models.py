from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) 
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name','last_name', 'phone', 'location']

    def __str__(self):
        return self.email

class OTP(models.Model):
    OTP_TYPE_CHOICES = (
        ("signup", "Signup Verification"),
        ("reset_password", "Reset Password"),)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.CharField(max_length=255)  # bcrypt hash
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPE_CHOICES, default='signup')

    def is_valid(self):
        """OTP صالح لمدة 5 دقائق ولم يُستخدم من قبل"""
        return (
            not self.is_used and
            timezone.now() - self.created_at < timedelta(minutes=5)
        )

    def __str__(self):
        return f"{self.otp_type} OTP for {self.user.email}"