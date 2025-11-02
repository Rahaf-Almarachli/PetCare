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
import bcrypt
from rest_framework.decorators import api_view, permission_classes

# 🟢 الاستيرادات لنظام النقاط 🟢
from reward_app.utils import award_points 
from activity.models import Activity 

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


# تهيئة سجل الأخطاء
logger = logging.getLogger(__name__)

# استخدام إعدادات البريد الإلكتروني من settings.py
DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL

# --- الثوابت (مفاتيح الأنشطة الموحدة) ---
PROFILE_COMPLETE_KEY = 'PROFILE_COMPLETE' 
ACCOUNT_VERIFIED_KEY = 'ACCOUNT_VERIFIED' 
# -------------------------------------------------------------------------


# ----------------------------------------------------
# 1. Signup Request
# ----------------------------------------------------
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
            logger.error(f"Email Error (Signup) to {email}: {e}")
            print(f"DEBUG: OTP failed to send via email. Code: {otp}")
            
        except Exception as e:
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

# ----------------------------------------------------
# 2. Signup Verification (منطق النقاط المعدل)
# ----------------------------------------------------
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
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        
        # 🟢 بداية المعاملة لتفعيل المستخدم ومنح النقاط 🟢
        points_awarded = 0
        current_points = 0
        
        with transaction.atomic():
            user.is_active = True
            user.save()
            otp_obj.is_used = True
            otp_obj.save()

            # 🛑 التعديل هنا: إعادة تحميل الكائن بعد الحفظ 🛑
            user.refresh_from_db() 

            # 🟢 منح نقاط التحقق من الحساب 🟢
            try:
                # 🛑 استخدام الصيغة الصحيحة التي تعيد نجاح العملية والنقاط الممنوحة
                success, points_awarded = award_points(
                    user=user, 
                    activity_system_name=ACCOUNT_VERIFIED_KEY,
                    description="Successfully verified account during signup."
                )
                
                # استرجاع الرصيد الحالي للمستخدم
                if success:
                    # بما أن award_points عملت، فالمحفظة موجودة ومحدثة
                    current_points = user.userwallet.total_points
                
                logger.info(f"Awarded points to {user.email} for account verification. Success: {success}")
                
            except Exception as e:
                logger.error(f"Failed to award points for verification to {user.email}: {e}")


        refresh = RefreshToken.for_user(user)
        user_profile_data = UserProfileSerializer(user).data
        
        return Response({
            "message": "Account verified successfully and points awarded.",
            "user": user_profile_data,
            "current_points": current_points,
            "points_awarded_now": points_awarded,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=status.HTTP_200_OK)


# ----------------------------------------------------
# 3. Login
# ----------------------------------------------------
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # 🛑🛑 التعديل هنا: تحديث حالة الكائن من DB لضمان الرصيد الأحدث 🛑🛑
        user.refresh_from_db() 
        
        refresh = RefreshToken.for_user(user)
        user_profile_data = UserProfileSerializer(user).data
        
        # 🟢 استرجاع رصيد النقاط (لإرساله في الرد) 🟢
        try:
            current_points = user.userwallet.total_points 
        except Exception:
            current_points = 0


        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user_profile_data,
            "current_points": current_points,
        })


# ----------------------------------------------------
# 4. Forget Password
# ----------------------------------------------------
class ForgetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic 
    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
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
            print(f"DEBUG: OTP failed to send via email (Reset). Code: {otp}")
            return Response({"message": "If a user with that email exists, an OTP has been generated (Email failed)."}, status=status.HTTP_200_OK) 
        except Exception as e:
            logger.error(f"General Error (Password Reset) to {email}: {e}")
            print(f"DEBUG: OTP failed to send via email (Reset). Code: {otp}")
            return Response({"message": "If a user with that email exists, an OTP has been generated (Email failed)."}, status=status.HTTP_200_OK)
        

# ----------------------------------------------------
# 5. Reset Password
# ----------------------------------------------------
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
                with transaction.atomic(): 
                    user.set_password(new_password)
                    user.save()
                    otp_obj.is_used = True
                    otp_obj.save()
                return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "OTP expired or already used."}, status=status.HTTP_400_BAD_REQUEST)


# ----------------------------------------------------
# 6. User Profile (تم التعديل لضمان النقاط الصحيحة)
# ----------------------------------------------------
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
        عند تحديث المستخدم لملفه الشخصي، نتحقق مما إذا كانت هذه أول مرة يكتمل فيها،
        فإذا كانت كذلك نمنحه نقاط مكافأة (إذا لم يحصل عليها من قبل).
        """
        user = self.get_object()
        
        # 🛑🛑 الكود المعدل يبدأ هنا: دالة التحقق الشامل (مع logs) 🛑🛑
        def is_profile_data_complete(user_obj):
            """
            تتحقق مما إذا كانت جميع الحقول المطلوبة (بما في ذلك الصورة المخزنة كـ URL نصي) مكتملة.
            """
            # الحقول النصية التي يجب أن تكون موجودة وغير فارغة
            required_fields = ['first_name', 'last_name', 'phone', 'location', 'profile_picture']
            
            # 🟢 أضف هذا السطر لمتابعة بداية الفحص
            logger.info(f"--- STARTING PROFILE COMPLETENESS CHECK for User {user_obj.email} ---")
            
            for field in required_fields:
                value = getattr(user_obj, field, None)
                
                # 🟢 أضف هذا السطر لتتبع قيمة كل حقل
                # ملاحظة: إذا كان الـ URL طويلاً، سيظهر كاملاً في اللوج
                logger.info(f"Checking field '{field}': Value is '{value}' (Type: {type(value)})")
                
                # التحقق من أن القيمة ليست None وليست سلسلة فارغة
                if not value or (isinstance(value, str) and value.strip() == ''):
                    # 🟢 أضف هذا السطر عند الفشل
                    logger.warning(f"PROFILE INCOMPLETE: Field '{field}' failed check.")
                    return False
                
            # 🟢 أضف هذا السطر عند النجاح
            logger.info("--- PROFILE CHECK SUCCESSFUL: All required fields are complete. ---")
            return True


        # 🟢 حفظ حالة اكتمال الملف قبل التحديث 🟢
        was_complete_before = is_profile_data_complete(user) # ⬅️ استخدام الدالة الجديدة
        
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # 1. حفظ البيانات الجديدة (داخل المعاملة الذرية)
        self.perform_update(serializer) 

        # إعادة تحميل الكائن لضمان الحصول على القيم الجديدة من قاعدة البيانات
        user.refresh_from_db() 
        
        # 2. 🟢 التحقق من إكمال الملف الشخصي بعد التحديث ومنح المكافأة 🟢
        
        # حالة اكتمال الملف الشخصي بعد التحديث
        is_complete_now = is_profile_data_complete(user) # ⬅️ استخدام الدالة الجديدة
        
        points_awarded = 0
        
        # يتم منح المكافأة فقط إذا أصبح الملف مكتملاً الآن ولم يكن مكتملاً من قبل
        if is_complete_now and not was_complete_before:
            try:
                success, points_awarded = award_points(
                    user=user,
                    activity_system_name=PROFILE_COMPLETE_KEY,
                    description='Profile completed for the first time.'
                )
                
                if success:
                    logger.info(f"Awarded {points_awarded} pts to {user.email} for profile completion.")
                
            except Exception as e:
                logger.error(f"Error awarding points to {user.email} for profile completion: {e}")


        # 3. استرجاع الرصيد الحالي للمستخدم (المحسوب)
        try:
            current_points = user.userwallet.total_points 
        except Exception:
            current_points = 0


        return Response({
            "message": "Profile updated successfully.",
            "user": UserProfileSerializer(user).data,
            "current_points": current_points,
            "points_awarded_now": points_awarded
        }, status=status.HTTP_200_OK)
        
    def perform_update(self, serializer):
        serializer.save()
# 🛑🛑 الكود المعدل ينتهي هنا 🛑🛑


# ----------------------------------------------------
# 7. Update Password
# ----------------------------------------------------
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

# ----------------------------------------------------
# 8. Email Change Request
# ----------------------------------------------------
class EmailChangeRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic 
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

# ----------------------------------------------------
# 9. Email Change Verify
# ----------------------------------------------------
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

# ----------------------------------------------------
# 10. Profile Picture & Name (لا تحتاج تعديلات نقاط)
# ----------------------------------------------------
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
        
        # 1. حفظ البيانات الجديدة
        serializer.save()
        
        return Response(
            {"message": "Profile picture updated successfully."}, 
            status=status.HTTP_200_OK
        )
        
class FullNameView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FullNameSerializer

    def get_object(self):
        return self.request.user

class FirstNameView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FirstNameSerializer

    def get_object(self):
        return self.request.user

# ----------------------------------------------------
# 11. API Root
# ----------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def api_root(request, format=None):
    return Response({"welcome to petcare api"})