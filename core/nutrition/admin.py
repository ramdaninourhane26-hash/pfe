from django.contrib import admin
from .models import Food
from .models import DietPlan, Meal, UserDietPlan
admin.site.register(Food)

admin.site.register(DietPlan)
admin.site.register(Meal)
admin.site.register(UserDietPlan)