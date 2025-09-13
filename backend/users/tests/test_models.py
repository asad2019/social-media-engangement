import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from decimal import Decimal

from users.models import User, SocialAccount, AuditLog

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'earner'
        }
    
    def test_user_creation(self):
        """Test user creation"""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.role, 'earner')
        self.assertEqual(user.wallet_balance, Decimal('0.00'))
        self.assertEqual(user.reputation_score, 0.0)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.kyc_status, 'not_required')
    
    def test_user_str_representation(self):
        """Test user string representation"""
        user = User.objects.create_user(**self.user_data)
        expected = f"{user.first_name} {user.last_name} ({user.username})"
        self.assertEqual(str(user), expected)
    
    def test_user_soft_delete(self):
        """Test user soft delete functionality"""
        user = User.objects.create_user(**self.user_data)
        user_id = user.id
        
        # Soft delete user
        user.soft_delete()
        
        # Check user is marked as deleted
        self.assertTrue(user.is_deleted)
        self.assertIsNotNone(user.deleted_at)
        
        # Check user is not in active queryset
        self.assertFalse(User.objects.filter(id=user_id).exists())
        self.assertTrue(User.all_objects.filter(id=user_id).exists())
    
    def test_user_can_withdraw(self):
        """Test user withdrawal eligibility"""
        user = User.objects.create_user(**self.user_data)
        
        # User with low balance should not be able to withdraw
        user.wallet_balance = Decimal('5.00')
        self.assertFalse(user.can_withdraw())
        
        # User with sufficient balance should be able to withdraw
        user.wallet_balance = Decimal('15.00')
        self.assertTrue(user.can_withdraw())
        
        # Inactive user should not be able to withdraw
        user.is_active = False
        self.assertFalse(user.can_withdraw())
    
    def test_user_kyc_required(self):
        """Test KYC requirement logic"""
        user = User.objects.create_user(**self.user_data)
        
        # User with low balance should not require KYC
        user.wallet_balance = Decimal('50.00')
        self.assertFalse(user.kyc_required())
        
        # User with high balance should require KYC
        user.wallet_balance = Decimal('150.00')
        self.assertTrue(user.kyc_required())


class SocialAccountModelTest(TestCase):
    """Test cases for SocialAccount model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_social_account_creation(self):
        """Test social account creation"""
        social_account = SocialAccount.objects.create(
            user=self.user,
            platform='instagram',
            username='test_instagram',
            account_url='https://instagram.com/test_instagram',
            follower_count=1000,
            is_verified=True
        )
        
        self.assertEqual(social_account.user, self.user)
        self.assertEqual(social_account.platform, 'instagram')
        self.assertEqual(social_account.username, 'test_instagram')
        self.assertEqual(social_account.follower_count, 1000)
        self.assertTrue(social_account.is_verified)
    
    def test_social_account_str_representation(self):
        """Test social account string representation"""
        social_account = SocialAccount.objects.create(
            user=self.user,
            platform='instagram',
            username='test_instagram'
        )
        expected = f"{self.user.username} - Instagram (@test_instagram)"
        self.assertEqual(str(social_account), expected)
    
    def test_social_account_soft_delete(self):
        """Test social account soft delete"""
        social_account = SocialAccount.objects.create(
            user=self.user,
            platform='instagram',
            username='test_instagram'
        )
        
        # Soft delete
        social_account.soft_delete()
        
        self.assertTrue(social_account.is_deleted)
        self.assertIsNotNone(social_account.deleted_at)


class AuditLogModelTest(TestCase):
    """Test cases for AuditLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_audit_log_creation(self):
        """Test audit log creation"""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='profile_update',
            description='Updated profile information',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0...',
            metadata={'field': 'email', 'old_value': 'old@example.com', 'new_value': 'new@example.com'}
        )
        
        self.assertEqual(audit_log.user, self.user)
        self.assertEqual(audit_log.action, 'profile_update')
        self.assertEqual(audit_log.description, 'Updated profile information')
        self.assertEqual(audit_log.ip_address, '192.168.1.1')
        self.assertIn('field', audit_log.metadata)
    
    def test_audit_log_str_representation(self):
        """Test audit log string representation"""
        audit_log = AuditLog.objects.create(
            user=self.user,
            action='profile_update',
            description='Updated profile information'
        )
        expected = f"{self.user.username} - profile_update: Updated profile information"
        self.assertEqual(str(audit_log), expected)


@pytest.mark.django_db
class UserModelPytestTest:
    """Pytest test cases for User model"""
    
    def test_user_creation_with_factory(self):
        """Test user creation using factory"""
        from factory import Factory
        from factory.django import DjangoModelFactory
        
        class UserFactory(DjangoModelFactory):
            class Meta:
                model = User
            
            username = 'factoryuser'
            email = 'factory@example.com'
            first_name = 'Factory'
            last_name = 'User'
            role = 'promoter'
        
        user = UserFactory()
        
        assert user.username == 'factoryuser'
        assert user.email == 'factory@example.com'
        assert user.role == 'promoter'
    
    def test_user_wallet_operations(self):
        """Test user wallet operations"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Test initial balance
        assert user.wallet_balance == Decimal('0.00')
        
        # Test balance update
        user.wallet_balance = Decimal('100.00')
        user.save()
        
        user.refresh_from_db()
        assert user.wallet_balance == Decimal('100.00')
    
    def test_user_role_permissions(self):
        """Test user role-based permissions"""
        promoter = User.objects.create_user(
            username='promoter',
            email='promoter@example.com',
            password='testpass123',
            role='promoter'
        )
        
        earner = User.objects.create_user(
            username='earner',
            email='earner@example.com',
            password='testpass123',
            role='earner'
        )
        
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role='admin'
        )
        
        # Test role assignments
        assert promoter.role == 'promoter'
        assert earner.role == 'earner'
        assert admin.role == 'admin'
        
        # Test role-based checks
        assert promoter.is_promoter()
        assert not promoter.is_earner()
        assert not promoter.is_admin()
        
        assert earner.is_earner()
        assert not earner.is_promoter()
        assert not earner.is_admin()
        
        assert admin.is_admin()
        assert not admin.is_promoter()
        assert not admin.is_earner()
