from django.db import models
from pets.models import Pet   # ربط مع جدول الحيوانات

class Vaccination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="vaccinations")
    vacc_name = models.CharField(max_length=100)
    vacc_date = models.DateField()
    vacc_certificate = models.ImageField(upload_to="vacc_certificates/", blank=True, null=True)

    def __str__(self):
        return f"{self.vacc_name} for {self.pet.pet_name}"

