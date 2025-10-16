"""
Django settings for PetCare project.
"""
from datetime import timedelta
from pathlib import Path
import os
#from dotenv import load_dotenv

# مكتبات التخزين وقاعدة البيانات
import dj_database_url
import cloudinary
from cloudinary.models import CloudinaryField 

# قم بتحميل متغيرات البيئة من ملف .env في جذر المشروع
#load_dotenv() 

# ----------------------------------------------------------------------
# 🏗️ BASE CONFIGURATION
# ----------------------------------------------------------------------

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')
AUTH_USER_MODEL = 'account.User'

# ----------------------------------------------------------------------
# 🔌 APPLICATION DEFINITION
# ----------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'account',
    'corsheaders',
    'pets',
    'adoption',
    'mating',
    'appointment',
    'vaccination',
    'django_filters',
    'storage',
    'rest_framework_nested',
    'mood',
    'alerts',
    'requests',
    
    # 🖼️ Cloudinary Storage
    'cloudinary_storage', 
    'cloudinary',
]

# ... (بقية إعدادات MIDDLEWARE و ROOT_URLCONF و TEMPLATES هي نفسها) ...

# ----------------------------------------------------------------------
# 🟢 DATABASE CONFIGURATION (Supabase/Render Migration) 🟢
# ----------------------------------------------------------------------

# الرابط الأساسي (Supabase في الإنتاج، أو الوجهة في الترحيل المحلي)
DATABASE_URL = os.environ.get("DATABASE_URL")

# رابط Render القديم (المصدر في الترحيل المحلي)
RENDER_OLD_URL = os.environ.get("RENDER_OLD_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        ),
    }
    
    # إضافة قاعدة بيانات Render القديمة كـ 'source'
    if RENDER_OLD_URL:
         DATABASES['source'] = dj_database_url.config(
             default=RENDER_OLD_URL,
             conn_max_age=600,
             ssl_require=True
         )
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ... (بقية إعدادات Password validation و Internationalization هي نفسها) ...

# ----------------------------------------------------------------------
# 🖼️ CLOUDINARY FILE STORAGE CONFIGURATION
# ----------------------------------------------------------------------

# 1. تحديد Cloudinary كواجهة تخزين افتراضية للملفات
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# 2. قراءة مفاتيح Cloudinary من متغيرات البيئة (ستقوم المكتبة بقراءتها تلقائياً)
# يجب عليك تعيين هذه المتغيرات الثلاثة في Render و/أو ملف .env محلياً
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# ملاحظة: تم حذف كتلة تكوين cloudinary.config() لأنها غالباً ما تكون غير ضرورية 
# عندما يتم تعريف CLOUDINARY_CLOUD_NAME و CLOUDINARY_API_KEY و CLOUDINARY_API_SECRET

# ----------------------------------------------------------------------
# 📁 STATIC AND MEDIA FILES
# ----------------------------------------------------------------------

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (هذه الإعدادات ضرورية لتحديد المسار المحلي فقط)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'