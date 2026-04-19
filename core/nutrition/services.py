from .models import UserDietPlan
from notifications.models import Notification


def buy_plan(user, diet_plan):
    user_plan = UserDietPlan.objects.create(
        user=user,
        diet_plan=diet_plan,
        status="active"
    )

    Notification.objects.create(
        user=user,
        message="Plan activated ✅"
    )

    return user_plan


def complete_plan(user_plan):
    user_plan.status = "completed"
    user_plan.save()

    Notification.objects.create(
        user=user_plan.user,
        message="Plan completed 🎉"
    )