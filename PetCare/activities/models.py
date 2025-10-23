from django.db import models
from django.contrib.auth import get_user_model
# نفترض وجود نموذج Pet في تطبيق آخر
from pets.models import Pet 

User = get_user_model()

# ====================
# 1. الأنشطة الثابتة التي تكسب نقاطاً
# ====================
class Activity(models.Model):
    """ يمثل الأنشطة التي تكسب نقاطاً (مثل: إكمال البروفايل). """
    name = models.CharField(max_length=100) # الاسم الذي يظهر للمستخدم (Complete your profile)
    # اسم فريد وثابت يستخدمه الكود لتحديد النشاط المكتمل
    SYSTEM_NAMES = (
        ('PROFILE_COMPLETE', 'Complete your profile'),
        ('ADOPT_PET', 'Adopt a pet'),
        ('PET_MATING', 'Pet Mating'),
    )
    system_name = models.CharField(max_length=50, choices=SYSTEM_NAMES, unique=True)
    points_value = models.IntegerField(default=0) # كم نقطة تُمنح
    
    def __str__(self):
        return self.name

# ====================
# 2. سجل اكتمال الأنشطة (لمنع التكرار)
# ====================
class ActivityLog(models.Model):
    """ يسجل متى تم إكمال نشاط لمرة واحدة للمستخدم. """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    completion_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        # ضمان أن المستخدم يمكنه إكمال كل نشاط لمرة واحدة فقط (إذا كان النشاط لمرة واحدة)
        unique_together = ('user', 'activity')

    def __str__(self):
        return f"{self.user.username} completed {self.activity.name}"