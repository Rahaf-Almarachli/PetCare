from django.db import models
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

class Pet(models.Model):
    
    COLOR_CHOICES = (
        ('Black', 'Black'),
        ('White','White'),
        ('Brown', 'Brown'),
        ('Grey','Grey'),
        ('Golden','Golden'),
        ('Tan','Tan'),
        ('Creamy','Creamy'),
        ('Cinamon','Cinamon'),
        ('Ginger','Ginger'),
        ('Silver','Silver')
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    pet_name = models.CharField(max_length=100)
    pet_type = models.CharField(max_length=50) 
    pet_color = models.CharField(max_length=50, choices=COLOR_CHOICES)
    pet_gender = models.CharField(max_length=20)
    pet_birthday = models.DateField()
    pet_photo = models.ImageField(upload_to='media/pets', blank=True, null=True)

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