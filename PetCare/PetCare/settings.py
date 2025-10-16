"""
Django settings for PetCare project.
"""
from datetime import timedelta
from pathlib import Path
import os
#from dotenv import load_dotenv

# مكتبات التخزين وقاعدة البيانات
import dj_database_url
# يجب أن تكون هذه المكتبات مثبتة في requirements.txt
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

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER",'rahaftest0@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD",'tyyu utct ggrx dipo')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 5

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
    
    # تطبيقات الطرف الثالث
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'rest_framework_nested',
    
    # 🖼️ Cloudinary Storage (تأكد من إضافتها هنا)
    'cloudinary_storage',
    'cloudinary',
    
    # تطبيقات المشروع
    'account',
    'pets',
    'adoption',
    'mating',
    'appointment',
    'vaccination',
    'storage',
    'mood',
    'alerts',
    'requests',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    "AUTH_TOKEN_CLASSES": ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ⚠️ تم تصحيح ترتيب Middleware هنا ليتوافق مع متطلبات Django و Admin
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # بعد Security
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware', # يجب أن يكون قبل Authentication
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'PetCare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'PetCare.wsgi.application'

# ----------------------------------------------------------------------
# 🟢 DATABASE CONFIGURATION (Supabase/Render Migration) 🟢
# ----------------------------------------------------------------------

DATABASE_URL = os.environ.get("DATABASE_URL")
RENDER_OLD_URL = os.environ.get("RENDER_OLD_URL")

if DATABASE_URL:
    DATABASES = {
        # 'default' هي قاعدة بيانات Supabase (التي سيستخدمها المشروع في الإنتاج)
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        ),
    }
    
    # إضافة قاعدة بيانات Render القديمة كـ 'source' إذا كنا نجري عملية الترحيل محلياً
    if RENDER_OLD_URL:
         DATABASES['source'] = dj_database_url.config(
             default=RENDER_OLD_URL,
             conn_max_age=600,
             ssl_require=True
         )
else:
    # استخدام SQLite للتطوير المحلي إذا لم يتم تعيين أي متغيرات بيئة
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ----------------------------------------------------------------------

# Password validation (بدون تغيير)
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization (بدون تغيير)
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------
# 🖼️ CLOUDINARY FILE STORAGE CONFIGURATION
# ----------------------------------------------------------------------

# 1. تحديد Cloudinary كواجهة تخزين افتراضية لملفات الوسائط
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# 2. قراءة مفاتيح Cloudinary من متغيرات البيئة (ستقوم المكتبة بقراءتها تلقائياً)
# يجب تعيين هذه المتغيرات الثلاثة في ملف .env محلياً وفي إعدادات Render 
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# ----------------------------------------------------------------------
# 📁 STATIC AND MEDIA FILES
# ----------------------------------------------------------------------

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# CORS (بدون تغيير)
CORS_ALLOW_ALL_ORIGINS = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'