from django.db import models

class Food(models.Model):
    name = models.CharField(max_length=100)
    calories = models.FloatField()

    def __str__(self):
        return self.name
from django.db import models
from django.contrib.auth.models import User

class DietPlan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    goal = models.CharField(max_length=100)
    duration_weeks = models.IntegerField()
    calories = models.IntegerField()

    def __str__(self):
        return self.name


class Meal(models.Model):
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name="meals")
    type = models.CharField(max_length=20)
    description = models.TextField()


class UserDietPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    diet_plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE)

    status = models.CharField(max_length=20, default="active")
    started_at = models.DateTimeField(auto_now_add=True)