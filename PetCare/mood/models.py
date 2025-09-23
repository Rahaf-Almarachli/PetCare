# petcare/models.py
from django.db import models
from django.utils import timezone
from pets.models import Pet



# Assuming your Pet model is already here
# from .models import Pet

class Mood(models.Model):
    mood = models.IntegerField()  # IntegerField to store the integer mood
    notes = models.TextField(blank=True, null=True)
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='moods')
    date = models.DateField() # Changed to DateField to store the date

    def __str__(self):
        return f"{self.pet.name}'s mood on {self.date}: {self.mood}"