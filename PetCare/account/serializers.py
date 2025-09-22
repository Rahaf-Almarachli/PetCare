from rest_framework import serializers
from .models import User


# -----------------------
# Signup
# -----------------------
class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'location', 'password', 'confirm_password']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(**validated_data)


# -----------------------
# Login
# -----------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate
        user = authenticate(email=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Invalid credentials.")
        data['user'] = user
        return data


# -----------------------
# Forget Password
# -----------------------
class ForgetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


# -----------------------
# Reset Password
# -----------------------
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data


# -----------------------
# Verify OTP (لتفعيل الحساب)
# -----------------------
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['full_name', 'first_name', 'last_name', 'phone', 'location', 'email']
        read_only_fields = ['full_name', 'email']

# User Profile (للعرض فقط)
class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['full_name','phone', 'location']
        read_only_fields = ['full_name']

# لتحديث الملف الشخصي (بما في ذلك الصورة)
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'location']
        
class ProfilePictureSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['profile_picture']

class FullNameSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ['full_name']

class FirstNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name']

# لتحديث كلمة المرور
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New password and confirmation do not match."})
        return data

# لتغيير البريد الإلكتروني (طلب)
class EmailChangeRequestSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)

# لتغيير البريد الإلكتروني (تحقق)
class EmailChangeVerifySerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    otp = serializers.CharField(required=True, max_length=6)