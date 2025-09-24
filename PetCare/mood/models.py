# mood/models.py
from django.db import models
from pets.models import Pet

class Mood(models.Model):
    mood = models.IntegerField()  # 1=Happy, 2=Active, 3=Calm, ... إلخ
    notes = models.TextField(blank=True, null=True)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='moods')
    date = models.DateField()  # نخزن التاريخ فقط

    def __str__(self):
        return f"{self.pet.pet_name}'s mood on {self.date}: {self.mood}"
