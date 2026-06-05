from rest_framework import serializers
from .models import TradeObject, InvestmentPlan, Investment


class InvestmentPlanSerializer(serializers.ModelSerializer):
    object_name = serializers.CharField(source='object.name', read_only=True)
    category = serializers.CharField(source='object.category', read_only=True)

    class Meta:
        model = InvestmentPlan
        fields = '__all__'


class TradeObjectSerializer(serializers.ModelSerializer):
    plans = InvestmentPlanSerializer(many=True, read_only=True)

    class Meta:
        model = TradeObject
        fields = '__all__'


class InvestmentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Investment
        fields = '__all__'
