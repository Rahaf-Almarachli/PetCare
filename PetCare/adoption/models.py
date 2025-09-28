from django.db import models
from pets.models import Pet

class AdoptionPost(models.Model):
    # علاقة OneToOne: حيوان واحد = منشور تبني واحد
    pet = models.OneToOneField(Pet, on_delete=models.CASCADE, related_name='adoption_post')
    owner_message = models.TextField() # رسالة المالك
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adoption post for {self.pet.pet_name}"