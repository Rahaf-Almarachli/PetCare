# petcare/models.py
from django.db import models
from django.utils.timezone import now
from pets.models import Pet

class Mood(models.Model):
    mood = models.IntegerField()  # رقم يعبر عن المزاج
    notes = models.TextField(blank=True, null=True)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='moods')
    date = models.DateField(default=now)  # يسجل تاريخ اليوم تلقائياً

    def __str__(self):
        return f"{self.pet.name}'s mood on {self.date}: {self.mood}"
