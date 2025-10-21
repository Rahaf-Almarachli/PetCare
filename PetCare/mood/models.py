from django.db import models
from pets.models import Pet

class Mood(models.Model):
    mood = models.IntegerField()
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='moods')
    date = models.DateField()

    def __str__(self):
        return f"{self.pet.pet_name}'s mood on {self.date}: {self.mood}"
