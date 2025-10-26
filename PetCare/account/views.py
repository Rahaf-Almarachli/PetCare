import random
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.db.utils import IntegrityError
from django.conf import settings
import smtplib 
import logging 
from socket import timeout as socket_timeout 
from smtplib import SMTPException, SMTPAuthenticationError 

# 🟢 الاستيرادات الجديدة لنظام النقاط 🟢
from rewards.utils import award_points
from activities.models import Activity, ActivityLog

from .models import User, OTP
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer,
    VerifyOTPSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    EmailChangeRequestSerializer,
    EmailChangeVerifySerializer,
    ProfilePictureSerializer,
    FullNameSerializer,
    FirstNameSerializer
)
import bcrypt

# تهيئة سجل الأخطاء
logger = logging.getLogger(__name__)

# استخدام إعدادات البريد الإلكتروني من settings.py
DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

# -----------------------
# Signup Request
# -----------------------
class SignupRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email")
        user_created = False 

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response(
                    {"error": "A user with this email already exists and is active."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            # إنشاء مستخدم جديد غير مفعّل (داخل المعاملة الذرية)
            user = User.objects.create_user(
                email=email,
                password=serializer.validated_data.get("password"),
                is_active=False,
                first_name=serializer.validated_data.get("first_name"),
                last_name=serializer.validated_data.get("last_name"),
                phone=serializer.validated_data.get("phone"),
                location=serializer.validated_data.get("location")
            )
            user_created = True

        # توليد وحفظ OTP
        otp = str(random.randint(100000, 999999))
        
        # تشفير وحفظ OTP
        hashed_otp = bcrypt.hashpw(otp.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        OTP.objects.filter(user=user, otp_type="signup").delete()
        OTP.objects.create(user=user, code=hashed_otp, otp_type="signup")

        # 🟢 محاولة إرسال البريد الإلكتروني 🟢
        email_sent = False
        email_subject = 'PetCare OTP Verification Code'
        email_message = f"Your OTP for PetCare registration is: {otp}"
        
        try:
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            email_sent = True
            logger.info(f"Successfully sent OTP to {email}")
            
        except (SMTPException, socket_timeout) as e:
            # التعامل مع أخطاء SMTP والمهلة
            logger.error(f"Email Error (Signup) to {email}: {e}")
            print(f"DEBUG: OTP failed to send via email. Code: {otp}")
            
        except Exception as e:
            # التعامل مع أي خطأ عام آخر
            logger.error(f"General Error (Signup) to {email}: {e}")
            print(f"DEBUG: OTP failed to send via email. Code: {otp}")

        
        # رسالة الرد تعتمد على الحالة
        if user_created:
            if email_sent:
                return Response(
                    {"message": "User created. OTP sent to your email."}, 
                    status=status.HTTP_201_CREATED
                )
            else:
                # إذا لم يُرسل الإيميل، نعطي رسالة واضحة ونبقى على حالة 201
                return Response(
                    {"message": "User created, but OTP email failed to send. Please check server logs for code."}, 
                    status=status.HTTP_201_CREATED
                )
        else:
            if email_sent:
                return Response(
                    {"message": "OTP re-sent to your email."}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"message": "OTP re-send failed. Please check server logs for code."}, 
                    status=status.HTTP_200_OK
                )

# -----------------------
# Signup Verification
# -----------------------
class SignupVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        user_input_otp = serializer.validated_data.get('otp')
        
        try:
            user = User.objects.get(email=email)
            otp_obj = OTP.objects.filter(user=user, otp_type='signup').latest('created_at')
        except (User.DoesNotExist, OTP.DoesNotExist):
            return Response({"error": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)

        
        # التحقق من الصلاحية والرمز
        if not otp_obj.is_valid() or not bcrypt.checkpw(user_input_otp.encode('utf-8'), otp_obj.code.encode('utf-8')):
             # يتم التحقق هنا من صلاحية الرمز وكونه غير مستخدم
             return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user.is_active = True
            user.save()
            otp_obj.is_used = True
            otp_obj.save()

        refresh = RefreshToken.for_user(user)
        user_profile_data = UserProfileSerializer(user).data
        
        return Response({
            "message": "Account verified successfully.",
            "user": user_profile_data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


# -----------------------
# Login
# -----------------------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        user_profile_data = UserProfileSerializer(user).data

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_profile_data,
        })


# -----------------------
# Forget Password
# -----------------------
class ForgetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic # تطبيق المعاملة الذرية
    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # رسالة عامة لأسباب أمنية
            return Response({"message": "If a user with that email exists, an OTP has been sent."}, status=status.HTTP_200_OK)

        # إنشاء وحفظ الـ OTP (ضمن المعاملة الذرية)
        otp = str(random.randint(100000, 999999))
        
        hashed_otp = bcrypt.hashpw(otp.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        OTP.objects.filter(user=user, otp_type='reset_password').delete()
        OTP.objects.create(user=user, code=hashed_otp, otp_type='reset_password')

        # 🟢 محاولة إرسال البريد الإلكتروني 🟢
        email_subject = 'PetCare Password Reset Code'
        email_message = f"Your Password Reset Code is: {otp}"
        
        try:
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({"message": "If a user with that email exists, an OTP has been sent."}, status=status.HTTP_200_OK)
            
        except (SMTPException, socket_timeout) as e:
            logger.error(f"Email Error (Password Reset) to {email}: {e}")
            # في حال فشل الإرسال، نعود إلى الرسالة العامة ونطبع الـ OTP في السجلات للمطور
            print(f"DEBUG: OTP failed to send via email (Reset). Code: {otp}")
            return Response({"message": "If a user with that email exists, an OTP has been generated (Email failed)."}, status=status.HTTP_200_OK) 
        except Exception as e:
            logger.error(f"General Error (Password Reset) to {email}: {e}")
            print(f"DEBUG: OTP failed to send via email (Reset). Code: {otp}")
            return Response({"message": "If a user with that email exists, an OTP has been generated (Email failed)."}, status=status.HTTP_200_OK)
        

# -----------------------
# Reset Password
# -----------------------
class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user_input_otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # البحث عن رمز إعادة تعيين كلمة المرور
            otp_obj = OTP.objects.filter(
                user=user, 
                otp_type='reset_password', 
                is_used=False
            ).latest('created_at')
        except OTP.DoesNotExist:
            return Response({"error": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_valid():
            if bcrypt.checkpw(user_input_otp.encode('utf-8'), otp_obj.code.encode('utf-8')):
                with transaction.atomic(): # استخدام معاملة للتأكد من تحديث كليهما
                    user.set_password(new_password)
                    user.save()
                    otp_obj.is_used = True
                    otp_obj.save()
                return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "OTP expired or already used."}, status=status.HTTP_400_BAD_REQUEST)


# -----------------------
# User Profile
# -----------------------
class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        عند تحديث المستخدم لملفه الشخصي، نتحقق مما إذا كانت هذه أول مرة يكتمل فيها.
        إذا كانت كذلك، نمنحه نقاط مكافأة (50 نقطة) باستخدام نظام Activities.
        """
        user = self.get_object()
        
        # 🟢 حفظ حالة اكتمال الملف قبل التحديث 🟢
        # نعتبر الملف كاملاً إذا كانت جميع الحقول المطلوبة مملوءة (قبل هذا التحديث)
        was_complete_before = all([
            user.first_name,
            user.last_name,
            user.phone,
            user.location,
            user.profile_picture # إذا كان الحقل اختياريًا، يمكنك إزالته
        ])
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # 1. حفظ البيانات الجديدة (داخل المعاملة الذرية)
        self.perform_update(serializer) # استخدام الدالة المدمجة

        # 2. 🟢 التحقق من إكمال الملف الشخصي بعد التحديث ومنح المكافأة 🟢
        
        # حالة اكتمال الملف الشخصي بعد التحديث
        is_complete_now = all([
            user.first_name,
            user.last_name,
            user.phone,
            user.location,
            user.profile_picture
        ])
        
        points_awarded = 0
        
        # يتم منح المكافأة فقط إذا أصبح الملف مكتملاً الآن ولم يكن مكتملاً من قبل
        if is_complete_now and not was_complete_before:
            try:
                # 🛑 اسم النشاط لمرة واحدة 🛑
                ACTIVITY_NAME = 'PROFILE_COMPLETE'
                
                activity = Activity.objects.get(system_name=ACTIVITY_NAME)
                
                # التحقق من أن المستخدم لم يكمل هذا النشاط بعد (لأنه يفترض أنه نشاط لمرة واحدة)
                if not ActivityLog.objects.filter(user=user, activity=activity).exists():
                    
                    # 2. منح النقاط الآمن
                    award_points(
                        user=user,
                        points=activity.points_value,
                        description=f'Task: {activity.name}'
                    )
                    points_awarded = activity.points_value
                    
                    # 3. تسجيل الإكمال لمنع التكرار (استخدام IntegrityError كحماية إضافية)
                    ActivityLog.objects.create(user=user, activity=activity)
                    logger.info(f"Awarded {points_awarded} pts to {user.email} for profile completion.")
                    
            except Activity.DoesNotExist:
                logger.error(f"Activity '{ACTIVITY_NAME}' not found in database. Check initial setup.")
            except IntegrityError:
                # نادر الحدوث بوجود شرط عدم التكرار أعلاه، ولكنه حماية إضافية
                logger.warning(f"User {user.email} attempted duplicate {ACTIVITY_NAME} award (Integrity Error).")

        # 4. استرجاع الرصيد الحالي للمستخدم (المحسوب)
        current_points = user.userwallet.total_points # يُفترض أن 'user' لديه related_name لـ UserWallet

        return Response({
            "message": "Profile updated successfully.",
            "user": UserProfileSerializer(user).data,
            "current_points": current_points,
            "points_awarded_now": points_awarded
        }, status=status.HTTP_200_OK)
    
    # -----------------------
    # الدالة الأساسية لحفظ التحديث
    # -----------------------
    def perform_update(self, serializer):
        serializer.save()


# -----------------------
# تحديث كلمة المرور
# -----------------------
class UpdatePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def put(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        old_password = serializer.validated_data.get('old_password')
        new_password = serializer.validated_data.get('new_password')
        
        if not user.check_password(old_password):
            return Response({"old_password": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

# -----------------------
# تغيير البريد الإلكتروني (طلب)
# -----------------------
class EmailChangeRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic # تطبيق المعاملة الذرية
    def post(self, request):
        serializer = EmailChangeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data.get('new_email')

        if User.objects.filter(email=new_email).exists():
            return Response({"error": "This email is already in use."}, status=status.HTTP_400_BAD_REQUEST)
        
        # توليد وحفظ OTP (ضمن المعاملة الذرية)
        otp = str(random.randint(100000, 999999))
        
        hashed_otp = bcrypt.hashpw(otp.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        OTP.objects.filter(user=request.user, otp_type="email_change").delete()
        OTP.objects.create(user=request.user, code=hashed_otp, otp_type="email_change")
        
        # 🟢 محاولة إرسال البريد الإلكتروني إلى البريد الجديد 🟢
        email_subject = 'PetCare Email Change Verification Code'
        email_message = f"Your Verification Code to change your email to {new_email} is: {otp}"
        
        try:
            send_mail(
                subject=email_subject,
                message=email_message,
                from_email=DEFAULT_FROM_EMAIL,
                recipient_list=[new_email], # الإرسال إلى الإيميل الجديد
                fail_silently=False,
            )
            return Response({"message": "Verification code sent to your new email."}, status=status.HTTP_200_OK)
            
        except (SMTPException, socket_timeout) as e:
            logger.error(f"Email Error (Email Change) to {new_email}: {e}")
            print(f"DEBUG: OTP failed to send via email (Email Change). Code: {otp}")
            return Response({"message": "Verification code generated (Email failed, check server logs)."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"General Error (Email Change) to {new_email}: {e}")
            print(f"DEBUG: OTP failed to send via email (Email Change). Code: {otp}")
            return Response({"message": "Verification code generated (Email failed, check server logs)."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -----------------------
# تغيير البريد الإلكتروني (تحقق)
# -----------------------
class EmailChangeVerifyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_email = serializer.validated_data.get('new_email')
        user_input_otp = serializer.validated_data.get('otp')
        
        try:
            otp_obj = OTP.objects.filter(user=request.user, otp_type="email_change").latest('created_at')
        except OTP.DoesNotExist:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not otp_obj.is_valid() or not bcrypt.checkpw(user_input_otp.encode('utf-8'), otp_obj.code.encode('utf-8')):
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = request.user
            user.email = new_email
            user.save()
            otp_obj.is_used = True
            otp_obj.save()
            
        return Response({"message": "Email updated successfully."}, status=status.HTTP_200_OK)

class ProfilePictureView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfilePictureSerializer

    def get_object(self):
        return self.request.user

class UpdateProfilePictureView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = ProfilePictureSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {"message": "Profile picture updated successfully."}, 
            status=status.HTTP_200_OK
        )
        
class FullNameView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FullNameSerializer

    def get_object(self):
        """
        يسترجع كائن المستخدم الحالي.
        """
        return self.request.user

class FirstNameView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FirstNameSerializer

    def get_object(self):
        """
        يعيد كائن المستخدم الحالي.
        """
        return self.request.user

# -----------------------
# API Root
# -----------------------
from rest_framework.decorators import api_view,permission_classes
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def api_root(request, format=None):
    return Response({"welcome to petcare api"})