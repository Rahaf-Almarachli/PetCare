from django.urls import path
from .views import (
    SignupRequestView,
    SignupVerifyView,
    LoginView,
    ForgetPasswordView,
    ResetPasswordView,
    UserProfileView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Signup (طلب OTP)
    path('signup/request/', SignupRequestView.as_view(), name='signup-request'),

    # Signup (التحقق من OTP وتفعيل الحساب)
    path('signup/verify/', SignupVerifyView.as_view(), name='signup-verify'),

    # Login
    path('login/', LoginView.as_view(), name='login'),

    # Forgot & Reset Password
    path('forgot-password/', ForgetPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # JWT Token (Obtain & Refresh)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]
