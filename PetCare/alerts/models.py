# alerts/models.py
from django.db import models
from django.conf import settings  # ✅ بدل من User الافتراضي

class Alert(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    name = models.CharField(max_length=100)  # اسم المنبّه
    time = models.TimeField()  # وقت التنبيه
    is_active = models.BooleanField(default=True)  # افتراضيًا ON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} at {self.time} ({'ON' if self.is_active else 'OFF'})"
