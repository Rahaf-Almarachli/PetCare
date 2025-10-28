# activities/migrations/000X_load_initial_activities.py

from django.db import migrations

def create_initial_activities(apps, schema_editor):
    """
    الدالة المسؤولة عن إنشاء الأنشطة الأساسية بشكل آمن.
    """
    # الحصول على النموذج 'Activity' من الحالة التاريخية للترحيل
    Activity = apps.get_model('activities', 'Activity')
    
    initial_activities = [
        # (system_name, name_ar, points, is_repeatable)
        ('PROFILE_COMPLETE', 'إكمال الملف الشخصي', 50, False),
        ('ADOPT_PET', 'تبني حيوان أليف بنجاح', 200, True),
        ('PET_MATING', 'عملية تزاوج ناجحة', 100, True),
    ]
    
    # نستخدم schema_editor.connection.alias لتجاوز مشاكل الاتصال أحياناً
    with schema_editor.connection.cursor() as cursor:
        for system_name, name, points, repeatable in initial_activities:
            # نستخدم get_or_create لتجنب تكرار السجلات
            Activity.objects.get_or_create(
                system_name=system_name,
                defaults={
                    'name': name,
                    'points_value': points,
                    'is_repeatable': repeatable
                }
            )

class Migration(migrations.Migration):

    dependencies = [
        # **هام**: استبدل '000X_previous_migration_name' بالاسم الحقيقي لآخر ملف ترحيل في activities
        ('activities', '0002_previous_migration_name'), 
    ]

    operations = [
        # هذا الأمر يشغل الدالة create_initial_activities
        migrations.RunPython(create_initial_activities, migrations.RunPython.noop),
    ]