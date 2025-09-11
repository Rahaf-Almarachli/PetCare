from django.db import models
from pets.models import Pet

class AdoptionPost(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE)
    additional_info = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adoption Post for {self.pet.name}"