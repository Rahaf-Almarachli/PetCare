from django.urls import path
from .views import (
    SignupRequestView,
    SignupVerifyView,
    LoginView,
    ForgetPasswordView,
    ResetPasswordView,
    UserProfileView,
    UpdatePasswordView,
    EmailChangeRequestView,
    EmailChangeVerifyView,
    UpdateProfilePictureView,
    FullNameView,
    FirstNameView
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
        # User Profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # تحديث كلمة المرور
    path('profile/update-password/', UpdatePasswordView.as_view(), name='update-password'),
    
    # تغيير البريد الإلكتروني
    path('profile/email-change-request/', EmailChangeRequestView.as_view(), name='email-change-request'),
    path('profile/email-change-verify/', EmailChangeVerifyView.as_view(), name='email-change-verify'),
    path('profile/picture/', UpdateProfilePictureView.as_view(), name='update-profile-picture'),
    path('profile/full-name/', FullNameView.as_view(), name='full-name'),
    path('profile/first-name/', FirstNameView.as_view(), name='first-name'),
]
