from django.db import models
from pets.models import Pet

class Appointment(models.Model):
    """
    Represents an appointment for a pet.
    يمثل موعدًا لحيوان أليف.
    """
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='appointments')
    service = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    provider = models.CharField(max_length=255)
    
    def __str__(self):
        return f"Appointment for {self.pet.pet_name} on {self.date}"

    class Meta:
        verbose_name_plural = "Appointments"
