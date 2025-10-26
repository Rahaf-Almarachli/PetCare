from django.apps import AppConfig
from django.db.utils import IntegrityError
import logging

logger = logging.getLogger(__name__)

class ActivitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activities'
    verbose_name = 'نظام الأنشطة والنقاط'

    def ready(self):
        """
        يتم تشغيل هذه الدالة عند إقلاع خادم Django (مرة واحدة).
        نستخدمها لضمان وجود الأنشطة الأساسية في قاعدة البيانات.
        """
        try:
            # نقوم باستيراد النموذج داخليًا لتجنب أخطاء الاستيراد المبكر
            from .models import Activity 
            
            self.create_initial_activities(Activity)
            
        except Exception as e:
            # تجاهل الأخطاء التي تحدث أثناء مرحلة الترحيل الأولى
            logger.warning(f"Skipping initial activities creation due to: {e}")

    def create_initial_activities(self, ActivityModel):
        """
        تقوم بإنشاء سجلات الأنشطة الأساسية.
        """
        initial_activities = [
            # (system_name, name_ar, points, is_repeatable)
            ('PROFILE_COMPLETE', 'إكمال الملف الشخصي', 50, False),
            ('ADOPT_PET', 'تبني حيوان أليف بنجاح', 200, True),
            ('PET_MATING', 'عملية تزاوج ناجحة', 100, True),
        ]
        
        created_count = 0
        
        for system_name, name, points, repeatable in initial_activities:
            try:
                # نستخدم get_or_create لضمان عدم تكرار إنشاء السجل إذا كان موجودًا
                _, created = ActivityModel.objects.get_or_create(
                    system_name=system_name,
                    defaults={
                        'name': name,
                        'points_value': points,
                        'is_repeatable': repeatable
                    }
                )
                if created:
                    created_count += 1
            except IntegrityError:
                # في حالة وجود خطأ في تزامن قاعدة البيانات، نطبعه ونكمل
                logger.error(f"Integrity error when creating activity: {system_name}")
            
        if created_count > 0:
            logger.info(f"Successfully created {created_count} initial activities on startup.")
