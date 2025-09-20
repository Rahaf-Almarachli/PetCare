from django.db import models
from django.contrib.auth.models import User

class Alert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    meal_name = models.CharField(max_length=255)
    alert_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.meal_name} for {self.user.username} at {self.alert_time}"