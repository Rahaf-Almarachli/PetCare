from django.db import models
from pets.models import Pet 
# افترض أن User هو المالك، ويمكن الوصول إليه عبر Pet.owner

class MatingPost(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='mating_post', unique=True)
    owner_message = models.TextField( max_length=500,blank=True,)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mating Post for {self.pet.pet_name}"