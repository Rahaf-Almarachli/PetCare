from django.urls import path
from .views import UserWalletDetailView

urlpatterns = [
    # GET: يعرض رصيد النقاط الكلي للمستخدم الحالي
    # مثال: /api/rewards/wallet/
    path('wallet/', UserWalletDetailView.as_view(), name='user-wallet-detail'),
]
