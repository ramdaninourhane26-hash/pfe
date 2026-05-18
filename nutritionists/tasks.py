# nutritionists/tasks.py
from celery import shared_task

@shared_task
def generate_checklist_for_plan(plan_id):
    plan = DietPlan.objects.get(id=plan_id)
    # ... même logique que ci-dessus

# nutritionists/tasks.py
from celery import shared_task
from datetime import datetime, timedelta
from consultations.models import Consultation
from .models import Notification

@shared_task
def create_consultation_reminders():
    upcoming = Consultation.objects.filter(
        date__gte=datetime.now(),
        date__lte=datetime.now() + timedelta(hours=1),
        status='pending'
    )
    created_count = 0
    for consultation in upcoming:
        _, created = Notification.objects.get_or_create(
            nutritionist=consultation.nutritionist,
            related_id=consultation.id,
            notification_type='consultation_reminder',
            defaults={
                'title': 'Upcoming Consultation',
                'message': f'Consultation with {consultation.patient.get_full_name()} in less than 1 hour.',
                'related_patient': consultation.patient,
            }
        )
        if created:
            created_count += 1
    return f"Created {created_count} reminders"