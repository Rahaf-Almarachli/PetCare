from django.db import migrations

def create_superuser(apps, schema_editor):
    User = apps.get_model('account', 'User')
    if not User.objects.filter(email="admin@petcare.com").exists():
        User.objects.create_superuser(
            email="admin@petcare.com",
            password="12345678",
            first_name="Admin",
            last_name="User",
            phone="0000000000",
            location="Default"
        )

class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),  # تأكدي إن اسم أول migration عندك صح
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]
