from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, SocialAccount, AuditLog


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'preferred_language', 'timezone'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            if user.is_deleted:
                raise serializers.ValidationError('User account is deleted')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    full_name_kyc = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'kyc_status', 'reputation_score', 'wallet_balance',
            'is_verified', 'preferred_language', 'timezone',
            'notification_preferences', 'full_name_kyc', 'created_at'
        ]
        read_only_fields = [
            'id', 'username', 'role', 'kyc_status', 'reputation_score',
            'wallet_balance', 'is_verified', 'created_at'
        ]


class UpdateProfileSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'preferred_language',
            'timezone', 'notification_preferences'
        ]


class KYCSerializer(serializers.ModelSerializer):
    """Serializer for KYC submission"""
    
    class Meta:
        model = User
        fields = [
            'first_name_kyc', 'last_name_kyc', 'date_of_birth',
            'address', 'phone_number', 'id_document_url', 'id_document_type'
        ]
    
    def validate_date_of_birth(self, value):
        from datetime import date
        if value and value >= date.today():
            raise serializers.ValidationError("Date of birth must be in the past")
        return value


class SocialAccountSerializer(serializers.ModelSerializer):
    """Serializer for social accounts"""
    
    class Meta:
        model = SocialAccount
        fields = [
            'id', 'platform', 'account_identifier', 'display_name',
            'verification_status', 'account_score', 'follower_count',
            'following_count', 'post_count', 'account_age_days',
            'last_activity', 'profile_picture_url', 'bio',
            'verified_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'verification_status', 'account_score', 'verified_at', 'created_at'
        ]


class SocialAccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating social accounts"""
    
    class Meta:
        model = SocialAccount
        fields = [
            'platform', 'account_identifier', 'display_name',
            'oauth_token', 'oauth_token_secret', 'oauth_refresh_token'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit logs"""
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'actor_username', 'action', 'target_type', 'target_id',
            'description', 'metadata', 'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password"""
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value, is_deleted=False)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user found with this email address')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password"""
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
