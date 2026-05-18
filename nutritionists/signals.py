# nutritionists/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DietPlan, PatientMealChecklist
from datetime import date, timedelta

@receiver(post_save, sender=DietPlan)
def create_meal_checklists(sender, instance, created, **kwargs):
    """Dès qu'un plan est créé/assigné, génère automatiquement la checklist"""
    if created or instance.is_active:
        # Calculer les dates du plan
        start = instance.start_date
        end = instance.end_date or (start + timedelta(days=30))
        
        # Pour chaque jour entre start et end
        current_date = start
        while current_date <= end:
            # Pour chaque repas du plan
            for meal in instance.meals.all():
                PatientMealChecklist.objects.get_or_create(
                    patient=instance.patient,
                    meal=meal,
                    date=current_date,
                    defaults={'status': 'pending'}
                )
            current_date += timedelta(days=1)
