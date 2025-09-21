from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import uuid

# مدير المستخدم المخصص
class UserManager(BaseUserManager):
    """
    مدير مستخدم مخصص للتعامل مع إنشاء المستخدمين والمستخدمين الخارقين.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        ينشئ ويحفظ مستخدمًا عاديًا بالبريد الإلكتروني وكلمة المرور المحددة.
        """
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        ينشئ ويحفظ مستخدمًا خارقًا بالبريد الإلكتروني وكلمة المرور المحددة.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
            
        return self.create_user(email, password, **extra_fields)

# نموذج المستخدم المخصص
class User(AbstractBaseUser, PermissionsMixin):
    """
    نموذج مستخدم مخصص بالاسم الأول، والاسم الأخير، والبريد الإلكتروني كمُعرّف.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # تعيين المدير المخصص
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """
        خاصية لحساب الاسم الكامل للمستخدم.
        """
        return f"{self.first_name} {self.last_name}".strip()

# نموذج OTP للتحقق
class OTP(models.Model):
    """
    نموذج لكلمة مرور لمرة واحدة (OTP) للتحقق من المستخدم.
    """
    OTP_TYPE_CHOICES = (
        ("signup", "Signup Verification"),
        ("reset_password", "Reset Password"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    code = models.UUIDField(default=uuid.uuid4, editable=False) # استخدام UUID لمزيد من الأمان
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
