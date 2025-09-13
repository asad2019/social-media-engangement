from rest_framework import serializers
from .models import Campaign, CampaignAnalytics
from users.models import User


class CampaignSerializer(serializers.ModelSerializer):
    promoter_name = serializers.CharField(source='promoter.username', read_only=True)
    total_jobs = serializers.SerializerMethodField()
    completed_jobs = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    remaining_budget = serializers.SerializerMethodField()
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'description', 'promoter', 'promoter_name',
            'engagement_type', 'platform', 'target_url', 'target_audience',
            'quantity', 'price_per_action', 'total_budget', 'reserved_funds',
            'remaining_budget', 'status', 'start_date', 'end_date',
            'created_at', 'updated_at', 'total_jobs', 'completed_jobs',
            'success_rate', 'metadata'
        ]
        read_only_fields = ['id', 'promoter', 'created_at', 'updated_at', 'reserved_funds']
    
    def get_total_jobs(self, obj):
        return obj.jobs.count()
    
    def get_completed_jobs(self, obj):
        return obj.jobs.filter(status='verified').count()
    
    def get_success_rate(self, obj):
        total_jobs = obj.jobs.count()
        if total_jobs == 0:
            return 0
        completed_jobs = obj.jobs.filter(status='verified').count()
        return round((completed_jobs / total_jobs) * 100, 2)
    
    def get_remaining_budget(self, obj):
        return obj.total_budget - obj.reserved_funds
    
    def validate(self, data):
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] >= data['end_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        if data.get('quantity') and data.get('price_per_action'):
            calculated_budget = data['quantity'] * data['price_per_action']
            if data.get('total_budget') and data['total_budget'] != calculated_budget:
                raise serializers.ValidationError("Total budget must match quantity × price per action")
        
        return data


class CampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            'title', 'description', 'engagement_type', 'platform',
            'target_url', 'target_audience', 'quantity', 'price_per_action',
            'total_budget', 'start_date', 'end_date', 'metadata'
        ]
    
    def validate_total_budget(self, value):
        if value <= 0:
            raise serializers.ValidationError("Total budget must be greater than 0")
        return value
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate_price_per_action(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price per action must be greater than 0")
        return value


class CampaignUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [
            'title', 'description', 'target_audience', 'end_date', 'metadata'
        ]
    
    def validate_end_date(self, value):
        if self.instance and self.instance.start_date:
            if value <= self.instance.start_date:
                raise serializers.ValidationError("End date must be after start date")
        return value


class CampaignAnalyticsSerializer(serializers.ModelSerializer):
    campaign_title = serializers.CharField(source='campaign.title', read_only=True)
    
    class Meta:
        model = CampaignAnalytics
        fields = [
            'id', 'campaign', 'campaign_title', 'total_views', 'total_clicks',
            'total_engagements', 'conversion_rate', 'cost_per_engagement',
            'roi', 'demographics', 'engagement_timeline', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CampaignPreviewSerializer(serializers.Serializer):
    engagement_type = serializers.ChoiceField(choices=Campaign.ENGAGEMENT_TYPE_CHOICES)
    platform = serializers.ChoiceField(choices=Campaign.PLATFORM_CHOICES)
    quantity = serializers.IntegerField(min_value=1)
    price_per_action = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    
    def validate(self, data):
        # Calculate total cost
        total_cost = data['quantity'] * data['price_per_action']
        platform_commission = total_cost * 0.05  # 5% platform commission
        final_cost = total_cost + platform_commission
        
        return {
            **data,
            'total_cost': total_cost,
            'platform_commission': platform_commission,
            'final_cost': final_cost
        }


class CostCalculatorSerializer(serializers.Serializer):
    engagement_type = serializers.ChoiceField(choices=Campaign.ENGAGEMENT_TYPE_CHOICES)
    platform = serializers.ChoiceField(choices=Campaign.PLATFORM_CHOICES)
    quantity = serializers.IntegerField(min_value=1)
    
    def calculate_cost(self):
        data = self.validated_data
        
        # Base prices per engagement type and platform
        base_prices = {
            'like': {'instagram': 0.10, 'twitter': 0.08, 'facebook': 0.12, 'tiktok': 0.15, 'youtube': 0.20, 'linkedin': 0.25},
            'follow': {'instagram': 0.25, 'twitter': 0.20, 'facebook': 0.30, 'tiktok': 0.35, 'youtube': 0.40, 'linkedin': 0.50},
            'comment': {'instagram': 0.30, 'twitter': 0.25, 'facebook': 0.35, 'tiktok': 0.40, 'youtube': 0.45, 'linkedin': 0.60},
            'share': {'instagram': 0.20, 'twitter': 0.15, 'facebook': 0.25, 'tiktok': 0.30, 'youtube': 0.35, 'linkedin': 0.40},
            'visit': {'website': 0.05},
            'subscribe': {'youtube': 0.50, 'tiktok': 0.40},
            'view': {'youtube': 0.15, 'tiktok': 0.20}
        }
        
        base_price = base_prices.get(data['engagement_type'], {}).get(data['platform'], 0.10)
        
        # Volume discounts
        quantity = data['quantity']
        if quantity >= 1000:
            discount = 0.15  # 15% discount for 1000+ engagements
        elif quantity >= 500:
            discount = 0.10  # 10% discount for 500+ engagements
        elif quantity >= 100:
            discount = 0.05  # 5% discount for 100+ engagements
        else:
            discount = 0
        
        discounted_price = base_price * (1 - discount)
        total_cost = quantity * discounted_price
        platform_commission = total_cost * 0.05  # 5% platform commission
        final_cost = total_cost + platform_commission
        
        return {
            'base_price': base_price,
            'discounted_price': discounted_price,
            'discount_percentage': discount * 100,
            'total_cost': total_cost,
            'platform_commission': platform_commission,
            'final_cost': final_cost,
            'cost_per_engagement': discounted_price
        }
