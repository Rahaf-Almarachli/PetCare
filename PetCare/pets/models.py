from django.db import models
from django.contrib.auth import get_user_model
from datetime import date
import uuid
from django.conf import settings

User = get_user_model()

class Pet(models.Model):
    
    COLOR_CHOICES = (
        ('Black', 'Black'), ('White','White'), ('Brown', 'Brown'),
        ('Grey','Grey'), ('Golden','Golden'), ('Tan','Tan'),
        ('Creamy','Creamy'), ('Cinamon','Cinamon'), ('Ginger','Ginger'),
        ('Silver','Silver')
    )
    TYPE_CHOICES = (
        ('Cat', 'Cat'), ('Dog', 'Dog')
    )

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    pet_name = models.CharField(max_length=100)
    pet_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    pet_color = models.CharField(max_length=50, choices=COLOR_CHOICES)
    pet_gender = models.CharField(max_length=20)
    pet_birthday = models.DateField()
    pet_photo = models.URLField(max_length=500, blank=True, null=True)

    # QR Data
    qr_token = models.CharField(max_length=100, unique=True, blank=True, null=True)
    qr_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.pet_name

    @property
    def age(self):
        today = date.today()
        age_in_years = today.year - self.pet_birthday.year
        if (today.month, today.day) < (self.pet_birthday.month, self.pet_birthday.day):
            age_in_years -= 1
        return age_in_years

    def generate_qr_data(self):
        """ينشئ رمز فريد ويبني رابط ثابت عند إنشاء الحيوان"""
        if not self.qr_token:
            self.qr_token = str(uuid.uuid4())

        # مثال: https://petcare-q9j0.onrender.com/api/pets/qr/<token>/
        domain = getattr(settings, 'SITE_DOMAIN', 'https://petcare-q9j0.onrender.com')
        self.qr_url = f"{domain}/api/pets/qr/{self.qr_token}/"

    def save(self, *args, **kwargs):
        if not self.qr_token or not self.qr_url:
            self.generate_qr_data()
        super().save(*args, **kwargs)
