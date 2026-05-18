# users/models.py
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
class UserProfile(models.Model):
    # 👇 'user_profile'
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_profile'  # ← Changement ici
    )

    SUBSCRIPTION_CHOICES = [
        ('free', 'Free (Blog only)'),
        ('standard', 'Standard Plan - Diet & AI'),
        ('premium', 'Premium Plan - Full Access')
    ]
    
    subscription_plan = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_CHOICES, 
        default='free'
    )
    payment_completed = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    weight = models.FloatField(default=70)
    height= models.FloatField(default=170)
    nutrition_streak = models.IntegerField(default=0)
    last_streak_date = models.DateField(null=True, blank=True)
    health_conditions = models.JSONField(default=list, blank=True)  
    goal = models.FloatField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)  
    has_diet_plan = models.BooleanField(default=False)
    has_ai_tracker = models.BooleanField(default=False)
    has_consultations = models.BooleanField(default=False)
    downloaded_plan_pdf = models.BooleanField(default=False)

    def get_bmi(self):
        if self.height > 0:
            return round(self.weight/ ((self.height / 100) ** 2), 1)
        return 0
    
    def get_bmi_category(self):
        bmi = self.get_bmi()
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal"
        elif bmi < 30:
            return "Overweight"
        return "Obese"
    
    def get_health_score(self):
        bmi = self.get_bmi()
        if 18.5 <= bmi <= 25:
            return 90
        elif 25 < bmi <= 30:
            return 70
        elif bmi > 30:
            return 50
        return 60

class WeightHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weight_history'  # ← Ajoute aussi ici
    )
    weight_kg = models.FloatField()
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['date']


class FoodLog(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='food_logs'
    )
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    food_name = models.CharField(max_length=200)
    calories = models.IntegerField()
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fats_g = models.FloatField(default=0)
    image = models.ImageField(upload_to='meals/', null=True, blank=True)
    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)
    
    class Meta:
        ordering = ['-logged_at']

class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.email} -> {self.receiver.email}: {self.content[:50]}"