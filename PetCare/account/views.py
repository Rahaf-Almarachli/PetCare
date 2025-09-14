import random
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OTP
from .serializers import (
    SignupSerializer,
    LoginSerializer,
    ForgetPasswordSerializer,
    ResetPasswordSerializer,
    VerifyOTPSerializer,
)
import bcrypt
from django.db import transaction
class SignupRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        
        # التحقق من وجود المستخدم مسبقاً
        if User.objects.filter(email=email).exists():
            return Response({"error": "A user with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # إنشاء مستخدم غير نشط
            user = User.objects.create_user(
                email=email,
                password=serializer.validated_data.get('password'),
                is_active=False,
                first_name=serializer.validated_data.get('first_name'),
                last_name=serializer.validated_data.get('last_name'),
                phone=serializer.validated_data.get('phone'),
                location=serializer.validated_data.get('location')
            )
            
            # إنشاء رمز OTP وإرساله
            otp = str(random.randint(100000, 999999))
            hashed_otp = bcrypt.hashpw(otp.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # حذف رموز OTP السابقة للمستخدم
            OTP.objects.filter(user=user).delete()
            
            OTP.objects.create(user=user, code=hashed_otp)

            send_mail(
                subject="Account Verification OTP",
                message=f"Your OTP for account verification is: {otp}",
                from_email="noreply@petcare.com",
                recipient_list=[email],
            )

        return Response({"message": "OTP sent for account verification."}, status=status.HTTP_201_CREATED)

class SignupVerifyView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data.get('email')
        user_input_otp = serializer.validated_data.get('otp')
        
        try:
            user = User.objects.get(email=email)
            otp_obj = OTP.objects.filter(user=user).latest('created_at')
        except (User.DoesNotExist, OTP.DoesNotExist):
            return Response({"error": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if not otp_obj.is_valid() or not bcrypt.checkpw(user_input_otp.encode('utf-8'), otp_obj.code.encode('utf-8')):
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user.is_active = True
            user.save()
            otp_obj.is_used = True
            otp_obj.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "Account verified successfully.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })

class ForgetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            #return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"message": "If a user with that email exists, an OTP has been sent."}, status=status.HTTP_200_OK)

        otp = str(random.randint(100000, 999999))
        hashed_otp = bcrypt.hashpw(otp.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        OTP.objects.filter(user=user).delete()
        OTP.objects.create(user=user, code=hashed_otp)

        send_mail(
            subject="Reset Password OTP",
            message=f"Your OTP is: {otp}",
            from_email="noreply@petcare.com",
            recipient_list=[email],
        )

        #return Response({"message": "OTP sent to your email."}, status=status.HTTP_200_OK)
        return Response({"message": "If a user with that email exists, an OTP has been sent."}, status=status.HTTP_200_OK)   

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
            #return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otp_obj = OTP.objects.filter(user=user, is_used=False).latest('created_at')
        except OTP.DoesNotExist:
            #return Response({"error": "No valid OTP found."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"error": "Invalid email or OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_valid():
            # استخدام bcrypt للتحقق من الرمز
            if bcrypt.checkpw(user_input_otp.encode('utf-8'), otp_obj.code.encode('utf-8')):
                user.set_password(new_password)
                user.save()
                otp_obj.is_used = True
                otp_obj.save()
                return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "OTP expired or already used."}, status=status.HTTP_400_BAD_REQUEST)
        
    
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes

@api_view(['GET,POST'])
@permission_classes([permissions.AllowAny])
def api_root(request, format=None):
    return Response({"signup": request.build_absolute_uri("/api/signup/request"),})
