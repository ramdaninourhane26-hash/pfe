from django.urls import path
from .views import get_my_plans, buy_diet_plan, complete_diet_plan

urlpatterns = [
    path("my-plans/", get_my_plans),
    path("buy/<int:plan_id>/", buy_diet_plan),
    path("complete/<int:user_plan_id>/", complete_diet_plan),
]