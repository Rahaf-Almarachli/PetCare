from django.urls import path
from .views import (
    SignupRequestView,
    SignupVerifyView,
    LoginView,
    ForgetPasswordView,
    ResetPasswordView
)
from rest_framework_simplejwt.views import TokenRefreshView

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

    # Refresh JWT Token
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
