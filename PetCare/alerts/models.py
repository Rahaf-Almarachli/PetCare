# alerts/models.py
from django.db import models
from django.contrib.auth.models import User
from pets.models import Pet


class Alert(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="alerts")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alerts")
    name = models.CharField(max_length=100)  # اسم المنبّه
    time = models.TimeField()  # وقت التنبيه
    is_active = models.BooleanField(default=True)  # افتراضيًا ON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} at {self.time} ({'ON' if self.is_active else 'OFF'})"
