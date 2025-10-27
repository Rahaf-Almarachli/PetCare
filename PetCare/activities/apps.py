# activities/apps.py

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db.utils import IntegrityError
import logging

logger = logging.getLogger(__name__)

# نعرّف الدالة خارج الكلاس حتى نتمكن من استخدامها في post_migrate signal
def create_initial_activities(sender, **kwargs):
    """
    تقوم بإنشاء سجلات الأنشطة الأساسية بعد اكتمال الترحيل.
    """
    # نتحقق لضمان أننا في التطبيق الصحيح
    if sender.label != 'activities':
        return

    try:
        from .models import Activity  # يتم الاستيراد هنا بعد الترحيل
    except ImportError:
        # إذا فشل الاستيراد، نخرج
        return
    
    initial_activities = [
        # (system_name, name_ar, points, is_repeatable)
        ('PROFILE_COMPLETE', 'إكمال الملف الشخصي', 50, False),
        ('ADOPT_PET', 'تبني حيوان أليف بنجاح', 200, True),
        ('PET_MATING', 'عملية تزاوج ناجحة', 100, True),
    ]
    
    created_count = 0
    
    for system_name, name, points, repeatable in initial_activities:
        try:
            _, created = Activity.objects.get_or_create(
                system_name=system_name,
                defaults={
                    'name': name,
                    'points_value': points,
                    'is_repeatable': repeatable
                }
            )
            if created:
                created_count += 1
        except Exception as e:
            # هنا يجب أن تكون قادرا على الوصول إلى قاعدة البيانات
            logger.error(f"FATAL DB ERROR when creating activity {system_name}: {e}")
            
    if created_count > 0:
        logger.info(f"Successfully created {created_count} initial activities using post_migrate.")
    else:
        logger.info("Initial activities already exist, skipping creation.")


class ActivitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activities'
    verbose_name = 'نظام الأنشطة والنقاط'

    def ready(self):
        # نقوم بربط الدالة create_initial_activities بإشارة post_migrate
        # مما يضمن تشغيلها فقط بعد اكتمال جميع الترحيلات
        post_migrate.connect(create_initial_activities, sender=self)