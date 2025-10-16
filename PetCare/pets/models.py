from django.db import models
from django.contrib.auth import get_user_model
from datetime import date
import uuid # جديد

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
    
    # حقل الصورة العادي (يتم إرسال الرابط من API الـ Storage)
    pet_photo = models.URLField(max_length=500, blank=True, null=True)
    
    # 💥 حقول QR الجديدة
    qr_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True,null=True, blank=True)
    qr_url = models.URLField(max_length=500, blank=True, null=True) # رابط صفحة المعلومات
    qr_code_image = models.URLField(max_length=500, blank=True, null=True) # رابط صورة QR
    

    def __str__(self):
        return self.pet_name
    
    @property
    def age(self):
        today = date.today()
        age_in_years = today.year - self.pet_birthday.year
        if today.month < self.pet_birthday.month or \
           (today.month == self.pet_birthday.month and today.day < self.pet_birthday.day):
             age_in_years -= 1
        return age_in_years