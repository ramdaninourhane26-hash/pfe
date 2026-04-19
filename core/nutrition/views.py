from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import DietPlan, UserDietPlan
from .serializers import DietPlanSerializer, UserDietPlanSerializer
from .services import buy_plan, complete_plan


@api_view(['GET'])
def get_my_plans(request):
    user = request.user

    active = UserDietPlan.objects.filter(user=user, status="active")
    past = UserDietPlan.objects.filter(user=user, status="completed")

    suggested = DietPlan.objects.exclude(
        id__in=active.values_list("diet_plan_id", flat=True)
    )

    return Response({
        "active": UserDietPlanSerializer(active, many=True).data,
        "past": UserDietPlanSerializer(past, many=True).data,
        "suggested": DietPlanSerializer(suggested, many=True).data,
    })


@api_view(['POST'])
def buy_diet_plan(request, plan_id):
    user = request.user
    plan = DietPlan.objects.get(id=plan_id)

    buy_plan(user, plan)

    return Response({"message": "Plan activated 🔥"})


@api_view(['POST'])
def complete_diet_plan(request, user_plan_id):
    user_plan = UserDietPlan.objects.get(id=user_plan_id)

    complete_plan(user_plan)

    return Response({"message": "Completed 🎉"})