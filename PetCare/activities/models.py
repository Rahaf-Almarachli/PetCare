from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

# -----------------
# 1. نموذج النشاط (Activity)
# يحدد قيمة النقاط واسم النظام (system_name)
# -----------------
class Activity(models.Model):
    name = models.CharField(max_length=100)
    # اسم فريد يُستخدم برمجياً في الكود (PROFILE_COMPLETE, ADOPT_PET)
    system_name = models.CharField(max_length=50, unique=True)
    points_value = models.PositiveIntegerField()
    # هل هذا النشاط قابل للتكرار أم لمرة واحدة؟
    is_repeatable = models.BooleanField(default=False) # الإعداد الافتراضي لمرة واحدة
    
    class Meta:
        verbose_name_plural = "Activities"
        
    def __str__(self):
        status = "Repeatable" if self.is_repeatable else "One-Time"
        return f"{self.name} (+{self.points_value} pts) [{status}]"

# -----------------
# 2. نموذج سجل إكمال النشاط (ActivityLog)
# يسجل متى أكمل المستخدم نشاطًا معينًا.
# -----------------
class ActivityLog(models.Model):
    """ يسجل متى أكمل المستخدم نشاطًا معينًا. """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    completion_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # هذا يضمن أن الأنشطة لمرة واحدة لا يمكن تسجيلها أكثر من مرة في قاعدة البيانات
        # (رغم أننا نطبق التحقق في الـ View، هذا حماية إضافية).
        unique_together = ('user', 'activity') 
        ordering = ['-completion_time']

    def __str__(self):
        return f"{self.user.email} completed {self.activity.name}"