from django.db import models
from django.conf import settings

# نستخدم الإعدادات لاستيراد نموذج المستخدم المخصص
User = settings.AUTH_USER_MODEL 

# ----------------------------------------------------
# 1. Activity (تعريف النشاط والمكافأة)
# ----------------------------------------------------
class Activity(models.Model):
    """
    يحدد نشاطًا يمكن أن يكسب نقاطًا (EARN) أو يمكن استبدال النقاط به (REDEEM).
    """
    INTERACTION_CHOICES = (
        ('EARN', 'Earning Points'),
        ('REDEEM', 'Redeem Points'),
    )
    
    # 🌟 حقل جديد: لتحديد ما إذا كان النشاط يمكن أن يمنح نقاطاً مرة واحدة فقط
    is_once_only = models.BooleanField(
        default=False, 
        verbose_name="Once Only Award",
        help_text="Check this if the user should only be awarded points for this activity once (e.g., Profile completion)."
    )

    name = models.CharField(max_length=255, verbose_name="Activity Name")
    # الاسم البرمجي (المفتاح): يجب أن يكون فريداً (مثل: COMPLETE_PROFILE, ADOPT_PET)
    system_name = models.CharField(max_length=50, unique=True, verbose_name="System Key")
    # قيمة النقاط: موجب للكسب، موجب للاستبدال (تكلفة الجائزة)
    points_value = models.IntegerField(verbose_name="Points Value") 
    
    interaction_type = models.CharField(
        max_length=10, 
        choices=INTERACTION_CHOICES,
        default='EARN',
        verbose_name="Interaction Type"
    )

    def __str__(self):
        type_prefix = "Cost" if self.interaction_type == 'REDEEM' else "Award"
        return f"{self.name} ({type_prefix}: {self.points_value} pts)"

    class Meta:
        verbose_name = "Activity/Reward Definition"
        verbose_name_plural = "Activity/Reward Definitions"

# ----------------------------------------------------
# 2. ActivityLog (سجل كسب النقاط)
# ----------------------------------------------------
class ActivityLog(models.Model):
    """
    سجل عندما ينجز مستخدم نشاطًا ويكسب نقاطًا.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    points_awarded = models.IntegerField(verbose_name="Points Awarded")
    created_at = models.DateTimeField(auto_now_add=True)
    
    description = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"{self.user.email} awarded {self.points_awarded} pts for {self.activity.name}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Points Earning Log"
        verbose_name_plural = "Points Earning Logs" 
        # ⚠️ القيد الفريد المعدل: لضمان عدم تكرار النشاط الذي يعطى مرة واحدة
        # unique_together = ('user', 'activity') 
        # تم إزالة هذا القيد بناءً على حاجتنا للسماح بالتكرار (مثل إضافة كلب) لكن تم إضافة حقل is_once_only أعلاه.
        # بدلاً من القيد، سيتم التحقق من حقل is_once_only داخل دالة award_points.