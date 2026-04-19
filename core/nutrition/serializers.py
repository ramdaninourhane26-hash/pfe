from rest_framework import serializers
from .models import DietPlan, Meal, UserDietPlan


class MealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meal
        fields = "__all__"


class DietPlanSerializer(serializers.ModelSerializer):
    meals = MealSerializer(many=True, read_only=True)

    class Meta:
        model = DietPlan
        fields = "__all__"


class UserDietPlanSerializer(serializers.ModelSerializer):
    diet_plan = DietPlanSerializer()

    class Meta:
        model = UserDietPlan
        fields = "__all__"