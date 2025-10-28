# activities/apps.py

from django.apps import AppConfig

class ActivitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activities'
    verbose_name = 'نظام الأنشطة والنقاط'

    # تم حذف دالة ready() ودوال تحميل البيانات بالكامل.
    # أصبح الكلاس نظيفاً وآمناً للإقلاع.
    pass