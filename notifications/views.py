from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from .models import DeviceToken # 💥 يجب أن يتوفر هذا النموذج (Model) 💥
from rest_framework import serializers

# ----------------------------------------------------
# Serializer بسيط للتحقق من البيانات (لأفضل ممارسات DRF)
# ----------------------------------------------------
class DeviceTokenSerializer(serializers.Serializer):
    """
    يُستخدم فقط للتحقق من أن حقل 'token' موجود و هو سلسلة نصية.
    """
    token = serializers.CharField(max_length=255, required=True)

# ----------------------------------------------------
# View لحفظ أو تحديث رمز الجهاز 
# ----------------------------------------------------
class RegisterDeviceTokenView(APIView):
    """
    POST: لتسجيل أو تحديث رمز الجهاز (FCM Token) الخاص بالمستخدم الحالي.
    يتطلب توثيق المستخدم (IsAuthenticated).
    """
    # يجب أن يكون المستخدم مسجلاً للدخول لإرسال الرمز
    permission_classes = [permissions.IsAuthenticated] 

    def post(self, request):
        # 1. استخدام Serializer للتحقق من صحة البيانات المرسلة
        serializer = DeviceTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # استخراج الرمز من البيانات الصحيحة
        token = serializer.validated_data['token']
        
        # 2. حفظ الرمز أو تحديثه
        # نستخدم update_or_create: 
        #   - إذا كان الرمز موجودًا، يتم تحديث is_active إلى True.
        #   - إذا لم يكن موجودًا، يتم إنشاء سجل جديد للمستخدم.
        device_token, created = DeviceToken.objects.update_or_create(
            # الشروط التي نعتمد عليها لتحديد السجل (user و token)
            user=request.user,
            token=token,
            # القيم التي يتم تعيينها أو تحديثها
            defaults={'is_active': True} 
        )

        # 3. إرجاع الاستجابة
        if created:
            message = "Token registered successfully."
            status_message = "created"
        else:
            message = "Token updated successfully."
            status_message = "updated"

        return Response({
            "message": message, 
            "status": status_message
        }, status=status.HTTP_200_OK)