from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import UserWallet
from .serializers import UserWalletSerializer # يجب أن تنشئ هذا السيريالايزر

# مثال على View لعرض المحفظة
class UserWalletDetailView(generics.RetrieveAPIView):
    """
    GET: عرض رصيد ونقاط المستخدم الحالي.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserWalletSerializer

    def get_object(self):
        # نقوم بجلب أو إنشاء محفظة المستخدم
        wallet, created = UserWallet.objects.get_or_create(user=self.request.user)
        return wallet
