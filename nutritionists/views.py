from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import DietPlan, Meal
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta,date
from consultations.models import Consultation, ActivityLog
from .models import PatientAssignment, Notification
from consultations.models import Consultation
from .models import DietPlan, Meal, PatientMealChecklist
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import PatientProgress
from django.http import JsonResponse


# nutritionists/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_diet_plan(request, plan_id):
    """Récupérer un plan spécifique"""
    return Response({'message': 'À implémenter'}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_patients(request):
    """Récupère UNIQUEMENT les patients assignés au nutritionniste"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    # ← FILTRE IMPORTANT : seulement les patients assignés à CE nutritionniste
    assignments = PatientAssignment.objects.filter(
        nutritionist=request.user,
        is_active=True
    ).select_related('patient')
    
    patients_data = []
    for assignment in assignments:
        patient = assignment.patient
        
        # Récupérer le profil du patient
        profile = getattr(patient, 'user_profile', None)
        
        # Calculer l'âge
        age = profile.age if profile and profile.age else 'N/A'
        
        # Récupérer le plan actif
        active_plan = DietPlan.objects.filter(
            patient=patient,
            is_active=True
        ).first()
        plan_name = active_plan.name if active_plan else 'No active plan'
        
        # Calculer le progrès
        total_meals = PatientMealChecklist.objects.filter(patient=patient).count()
        completed_meals = PatientMealChecklist.objects.filter(patient=patient, status='completed').count()
        progress = round((completed_meals / total_meals) * 100) if total_meals > 0 else 0
        
        # Dernière consultation
        last_consultation = Consultation.objects.filter(
            patient=patient,
            nutritionist=request.user
        ).order_by('-date').first()
        last_visit = last_consultation.date.strftime('%b %d, %Y') if last_consultation else 'No visits'
        
        patients_data.append({
            'id': patient.id,
            'name': patient.get_full_name() or patient.email.split('@')[0],
            'email': patient.email,
            'age': age,
            'plan': plan_name,
            'progress': progress,
            'last_visit': last_visit,
            'avatar': patient.first_name[0] if patient.first_name else 'U'
        })
    
    return Response(patients_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionist_stats(request):
    nutritionist = request.user
    
    if nutritionist.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    # 1. Patients actifs avec leur taux d'adhérence
    assignments = PatientAssignment.objects.filter(
        nutritionist=nutritionist,
        is_active=True
    ).select_related('patient')
    
    patient_names = []
    adherence_rates = []
    
    for assignment in assignments:
        patient = assignment.patient
        patient_names.append(patient.get_full_name() or patient.email.split('@')[0])
        
        # Calculer le taux d'adhérence (exemple: basé sur les repas complétés)
        # À adapter selon ta logique métier
       
        total_meals = PatientMealChecklist.objects.filter(patient=patient).count()
        completed_meals = PatientMealChecklist.objects.filter(patient=patient, status='completed').count()
        rate = round((completed_meals / total_meals) * 100) if total_meals > 0 else 0
        adherence_rates.append(rate)
    
    # 2. Consultations du jour
    today = timezone.now().date()
    today_consultations = Consultation.objects.filter(
        nutritionist=nutritionist,
        date__date=today
    )
    today_count = today_consultations.count()
    completed_today = today_consultations.filter(status='completed').count()
    upcoming_today = today_consultations.filter(status='pending', date__gte=timezone.now()).count()
    
    # 3. Messages non lus (à implémenter)
    pending_messages = 0
    
    # 4. Earnings (exemple)
    earnings_mtd = 3240
    earnings_change = '+12% vs last month'
    
    # 5. Recent activities
    recent_activities = ActivityLog.objects.filter(nutritionist=nutritionist)[:10]
    activities_list = []
    for activity in recent_activities:
        activities_list.append({
            'type': activity.activity_type,
            'description': activity.description,
            'time_ago': get_time_ago(activity.created_at),
        })
    
    if not activities_list:
        activities_list = [
            {'type': 'patient_assigned', 'description': 'New patient assigned', 'time_ago': '2 hours ago'},
            {'type': 'message_sent', 'description': 'Message from patient', 'time_ago': '5 hours ago'},
        ]
    
    return Response({
        'nutritionist_name': nutritionist.get_full_name() or nutritionist.email.split('@')[0],
        'specialization': nutritionist.specialization or 'Clinical Nutritionist',
        'email': nutritionist.email,
        'active_patients': len(patient_names),
        'active_patients_change': '+3 this month',
        'today_consultations': today_count,
        'today_consultations_detail': f'{completed_today} completed, {upcoming_today} upcoming',
        'pending_messages': pending_messages,
        'earnings_mtd': earnings_mtd,
        'earnings_change': earnings_change,
        'adherence_chart': {
            'labels': patient_names,
            'rates': adherence_rates,
        },
        'recent_activities': activities_list
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionist_patients(request):
    """Récupère la liste des patients du nutritionniste"""
    nutritionist = request.user
    
    assignments = PatientAssignment.objects.filter(
        nutritionist=nutritionist,
        is_active=True
    ).select_related('patient')
    
    patients_data = []
    for assignment in assignments:
        patient = assignment.patient
        profile = getattr(patient, 'user_profile', None)
        
        # Compter les consultations
        consultations_count = Consultation.objects.filter(
            patient=patient,
            nutritionist=nutritionist
        ).count()
        
        patients_data.append({
            'id': patient.id,
            'name': patient.get_full_name(),
            'email': patient.email,
            'avatar': patient.first_name[0] if patient.first_name else 'U',
            'last_visit': get_last_visit(patient, nutritionist),
            'consultations': consultations_count,
            'status': 'active'
        })
    
    return Response(patients_data)

def get_time_ago(dt):
    """Calcule le temps écoulé depuis une date"""
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return 'Yesterday'
        return f'{diff.days} days ago'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} hours ago'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} minutes ago'
    else:
        return 'Just now'

def get_last_visit(patient, nutritionist):
    """Récupère la dernière consultation ou activité"""
    last_consultation = Consultation.objects.filter(
        patient=patient,
        nutritionist=nutritionist
    ).order_by('-date').first()
    
    if last_consultation:
        return get_time_ago(last_consultation.date)
    return 'Never'


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications(request):
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    notifications = Notification.objects.filter(
        nutritionist=request.user,
        is_read=False
    )[:20]
    
    return Response({
        'notifications': [
            {
                'id': n.id,
                'type': n.notification_type,
                'title': n.title,
                'message': n.message,
                'patient_name': n.related_patient.get_full_name() if n.related_patient else None,
                'time_ago': get_time_ago(n.created_at),
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ],
        'unread_count': notifications.count()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, notification_id):
    from .models import Notification
    
    try:
        notification = Notification.objects.get(id=notification_id, nutritionist=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Not found'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    from .models import Notification
    
    Notification.objects.filter(nutritionist=request.user, is_read=False).update(is_read=True)
    return Response({'message': 'All notifications marked as read'})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consultation_requests(request):
    """Récupère les demandes de consultation en attente"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    requests = Consultation.objects.filter(
        nutritionist=request.user,
        status='requested'
    ).select_related('patient')
    
    return Response([
        {
            'id': c.id,
            'patient_name': c.patient.get_full_name() or c.patient.email,
            'patient_email': c.patient.email,
            'date': c.date.isoformat(),
            'date_display': c.date.strftime('%b %d, %Y • %I:%M %p'),
            'notes': c.notes,
            'created_at': c.created_at.isoformat(),
        }
        for c in requests
    ])

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_consultation(request, consultation_id):
    """Confirme ou refuse une consultation"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        consultation = Consultation.objects.get(id=consultation_id, nutritionist=request.user)
    except Consultation.DoesNotExist:
        return Response({'error': 'Consultation not found'}, status=404)
    
    action = request.data.get('action')  # 'confirm' or 'reject'
    explanation = request.data.get('explanation', '')
    
    if action == 'confirm':
        consultation.status = 'confirmed'
        consultation.confirmed_at = timezone.now()
        message = f"✅ Your consultation on {consultation.date.strftime('%b %d at %I:%M %p')} has been confirmed by {request.user.get_full_name()}."
        title = 'Consultation Confirmed'
    elif action == 'reject':
        consultation.status = 'rejected'
        message = f"❌ Your consultation request for {consultation.date.strftime('%b %d at %I:%M %p')} was not accepted. Reason: {explanation}"
        title = 'Consultation Request Update'
    else:
        return Response({'error': 'Invalid action'}, status=400)
    
    consultation.save()
    
    # Créer une notification pour le patient
    Notification.objects.create(
        user=consultation.patient,
        notification_type='consultation_update',
        title=title,
        message=message,
        related_id=consultation.id,
    )
    
    return Response({'message': f'Consultation {action}ed successfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionist_consultations(request):
    """Récupère les consultations du nutritionniste (upcoming + past)"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    now = timezone.now()
    
    upcoming = Consultation.objects.filter(
        nutritionist=request.user,
        status='confirmed',
        date__gte=now
    ).order_by('date')
    
    past = Consultation.objects.filter(
        nutritionist=request.user,
        status='completed'
    ).order_by('-date')[:20]
    
    return Response({
        'upcoming': [
            {
                'id': c.id,
                'patient_name': c.patient.get_full_name() or c.patient.email,
                'date_display': c.date.strftime('%b %d, %Y • %I:%M %p'),
                'date_iso': c.date.isoformat(),
                'type': 'Zoom Call',
                'zoom_link': c.zoom_link,
            }
            for c in upcoming
        ],
        'past': [
            {
                'id': c.id,
                'patient_name': c.patient.get_full_name() or c.patient.email,
                'date_display': c.date.strftime('%b %d, %Y'),
                'duration': '60 min',
                'notes': c.nutritionist_notes,
            }
            for c in past
        ]
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_consultation(request, consultation_id):
    """Marque une consultation comme terminée"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    try:
        consultation = Consultation.objects.get(id=consultation_id, nutritionist=request.user)
    except Consultation.DoesNotExist:
        return Response({'error': 'Consultation not found'}, status=404)
    
    consultation.status = 'completed'
    consultation.nutritionist_notes = request.data.get('notes', '')
    consultation.save()
    
    # Notification au patient
    Notification.objects.create(
        user=consultation.patient,
        notification_type='consultation_completed',
        title='Consultation Completed',
        message=f'Your consultation with {request.user.get_full_name()} on {consultation.date.strftime("%b %d")} has been marked as completed.',
        related_id=consultation.id,
    )
    
    return Response({'message': 'Consultation marked as completed'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionist_calendar(request):
    """Récupère les consultations pour le calendrier du nutritionniste"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    from consultations.models import Consultation
    from django.utils import timezone
    
    # Récupérer les consultations confirmées des 7 prochains jours
    consultations = Consultation.objects.filter(
        nutritionist=request.user,
        status='confirmed',
        date__gte=timezone.now(),
        date__lte=timezone.now() + timezone.timedelta(days=7)
    ).order_by('date').select_related('patient')
    
    # Grouper par date
    events_by_date = {}
    
    for c in consultations:
        date_key = c.date.date().isoformat()
        if date_key not in events_by_date:
            events_by_date[date_key] = []
        events_by_date[date_key].append({
            'type': 'consultation',
            'patient_name': c.patient.get_full_name() or c.patient.email.split('@')[0],
            'time': c.date.strftime('%H:%M'),
            'zoom_link': c.zoom_link,
        })
    
    return Response({
        'events_by_date': events_by_date,
    })

def generate_meal_checklist(plan):
    """Génère la checklist quotidienne pour le patient"""
    current_date = plan.start_date
    end_date = plan.end_date or (plan.start_date + timedelta(days=30))
    
    while current_date <= end_date:
        for meal in plan.meals.all():
            PatientMealChecklist.objects.get_or_create(
                patient=plan.patient,
                meal=meal,
                date=current_date,
                defaults={
                    'meal_name': f"{meal.get_meal_type_display()}: {meal.food_name}",
                    'meal_time': '12:00',
                    'status': 'pending'
                }
            )
        current_date += timedelta(days=1)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_diet_plan(request):
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    if request.method == 'GET':
        # Retourner la liste des plans
        plans = DietPlan.objects.filter(nutritionist=request.user).order_by('-created_at')
        return Response([
            {
                'id': p.id,
                'name': p.name,
                'patient_name': p.patient.get_full_name() or p.patient.email.split('@')[0] if p.patient else 'Public Plan',
                'start_date': p.start_date,
                'end_date': p.end_date,
                'is_active': p.is_active,
                'is_public': getattr(p, 'is_public', False)
            }
            for p in plans
        ])
    
    elif request.method == 'POST':
        data = request.data
        plan_type = data.get('plan_type', 'personalized')  # 'personalized' or 'standard'
        
        if plan_type == 'personalized':
            # Plan personnalisé pour un patient spécifique
            plan = DietPlan.objects.create(
                nutritionist=request.user,
                patient_id=data['patient_id'],
                name=data['name'],
                description=data.get('description', ''),
                start_date=data['start_date'],
                end_date=data.get('end_date'),
                is_active=True
            )
            
            for meal_data in data.get('meals', []):
                Meal.objects.create(
                    plan=plan,
                    meal_type=meal_data['meal_type'],
                    food_name=meal_data['food_name'],
                    quantity=meal_data.get('quantity', ''),
                    calories=meal_data.get('calories', 0),
                    order=meal_data.get('order', 0)
                )
            
            generate_meal_checklist(plan)
            
            Notification.objects.create(
                user=plan.patient,
                notification_type='plan_updated',
                title='New Diet Plan Assigned 🥗',
                message=f'{request.user.get_full_name()} has assigned you a new diet plan: "{plan.name}". Check your diet plans section!',
                related_id=plan.id,
            )
            
            return Response({'message': 'Personalized plan created successfully', 'plan_id': plan.id}, status=201)
        
        elif plan_type == 'standard':
            # Plan standard (public) - à valider par admin
            # Créer un SpecialOffer en attente
            special_offer = SpecialOffer.objects.create(
                name=data['name'],
                short_description=data.get('short_description', ''),
                description=data.get('description', ''),
                price=data['price'],
                original_price=data.get('original_price'),
                features=data.get('features', []),
                icon=data.get('icon', '🍽️'),
                offer_type='diet_plan',
                is_active=False,  # En attente de validation
                submitted_by=request.user,  
                submitted_at=timezone.now(),
                valid_until=timezone.now().date() + timedelta(days=365)
            )
            
            # Option: notifier l'admin
            # Notification.objects.create(...)
            
            return Response({
                'message': 'Standard plan submitted for admin approval', 
                'offer_id': special_offer.id
            }, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionist_patients_for_select(request):
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    assignments = PatientAssignment.objects.filter(
        nutritionist=request.user,
        is_active=True
    ).select_related('patient')
    
    return Response([
        {
            'id': a.patient.id,
            'name': a.patient.get_full_name() or a.patient.email.split('@')[0],
            'email': a.patient.email,
        }
        for a in assignments
    ])

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionist_diet_plans(request):
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    plans = DietPlan.objects.filter(
        nutritionist=request.user
    ).order_by('-created_at')
    
    return Response([
        {
            'id': p.id,
            'name': p.name,
            'patient_name': p.patient.get_full_name() or p.patient.email.split('@')[0],
            'start_date': p.start_date,
            'end_date': p.end_date,
            'is_active': p.is_active,
        }
        for p in plans
    ])

@login_required
@require_http_methods(["GET"])
def get_patient_progress(request, patient_id):
    """Récupère l'historique des progrès d'un patient depuis WeightHistory"""
    from django.contrib.auth import get_user_model
    from users.models import WeightHistory
    User = get_user_model()
    
    try:
        # Vérifier l'accès
        is_assigned = PatientAssignment.objects.filter(
            nutritionist=request.user,
            patient_id=patient_id,
            is_active=True
        ).exists()
        
        if not is_assigned:
            return JsonResponse({'error': 'Patient not assigned to you'}, status=403)
        
        patient = User.objects.get(id=patient_id)
        profile = getattr(patient, 'user_profile', None)
        
        # Récupérer l'historique des poids depuis WeightHistory (comme dans userdash)
        weight_history = WeightHistory.objects.filter(user=patient).order_by('date')
        
        # Période
        period = request.GET.get('period', '3m')
        period_days = {'1m': 30, '3m': 90, '6m': 180, '1y': 365, 'all': 9999}
        cutoff_days = period_days.get(period, 90)
        cutoff_date = timezone.now().date() - timedelta(days=cutoff_days)
        
        # Filtrer par période
        filtered = [entry for entry in weight_history if entry.date >= cutoff_date]
        
        # Construire les données
        if filtered:
            labels = [entry.date.strftime('%d/%m') for entry in filtered]
            weight_data = [float(entry.weight_kg) for entry in filtered]
            
            # Body fat - à ajouter si tu as un modèle BodyFatHistory, sinon simulé
            body_fat_data = []
            for entry in filtered:
                # Si tu as body_fat dans WeightHistory, utilise-le
                if hasattr(entry, 'body_fat') and entry.body_fat:
                    body_fat_data.append(float(entry.body_fat))
                else:
                    # Simuler body_fat basé sur le poids (optionnel)
                    bf = round(entry.weight_kg * 0.35, 1)
                    body_fat_data.append(bf)
            
            current_weight = float(filtered[-1].weight_kg)
            first_weight = float(filtered[0].weight_kg)
            
            weight_change = round(current_weight - first_weight, 1)
            weight_change_percent = round(abs((weight_change / first_weight) * 100), 1) if first_weight > 0 else 0
            
            current_body_fat = body_fat_data[-1] if body_fat_data else None
            first_body_fat = body_fat_data[0] if body_fat_data else None
            fat_change = round(current_body_fat - first_body_fat, 1) if current_body_fat and first_body_fat else 0
            
        else:
            # Pas d'historique : utiliser le poids actuel du profil
            labels = []
            weight_data = []
            body_fat_data = []
            current_weight = float(profile.weight) if profile and profile.weight else None
            weight_change = 0
            weight_change_percent = 0
            current_body_fat = None
            fat_change = 0
        
        goal_weight = float(profile.goal) if profile and profile.goal else None
        to_goal = round(goal_weight - current_weight, 1) if goal_weight and current_weight else 0
        
        # Si pas assez de données, générer une petite simulation (optionnel)
        if len(weight_data) < 2 and current_weight:
            # Utiliser les dernières semaines
            import random
            random.seed(patient_id)
            labels = []
            weight_data = []
            for i in range(6):
                date = timezone.now().date() - timedelta(days=(5-i)*7)
                labels.append(date.strftime('%d/%m'))
                simulated_weight = current_weight - (5-i) * 0.5
                weight_data.append(round(simulated_weight, 1))
            weight_change = weight_data[-1] - weight_data[0]
            weight_change_percent = round(abs((weight_change / weight_data[0]) * 100), 1) if weight_data[0] > 0 else 0
            body_fat_data = [round(w * 0.35, 1) for w in weight_data]
            current_body_fat = body_fat_data[-1]
            fat_change = round(body_fat_data[-1] - body_fat_data[0], 1)
        
        response_data = {
            'labels': labels,
            'weight_data': weight_data,
            'body_fat_data': body_fat_data,
            'current_weight': current_weight,
            'current_body_fat': current_body_fat,
            'goal_weight': goal_weight,
            'weight_change': weight_change,
            'weight_change_percent': weight_change_percent,
            'fat_change': fat_change,
            'to_goal': to_goal,
            'to_goal_text': f'{abs(to_goal)} kg to goal' if goal_weight else 'No goal set'
        }
        
        print("Progress data from WeightHistory:", response_data)
        return JsonResponse(response_data)
        
    except Exception as e:
        print("Error in get_patient_progress:", str(e))
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def add_patient_progress(request, patient_id):
    """Ajoute une nouvelle mesure de progrès"""
    import json
    try:
        data = json.loads(request.body)
        
        progress = PatientProgress.objects.create(
            patient_id=patient_id,
            nutritionist=request.user,
            weight=data.get('weight'),
            body_fat=data.get('body_fat'),
            muscle_mass=data.get('muscle_mass'),
            notes=data.get('notes', '')
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Progress recorded successfully',
            'id': progress.id
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patients_for_progress(request):
    """Récupère la liste des patients assignés pour le select"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    assignments = PatientAssignment.objects.filter(
        nutritionist=request.user,
        is_active=True
    ).select_related('patient')
    
    # Format attendu par le frontend: {id: xxx, name: xxx}
    patients_data = []
    for assignment in assignments:
        patient = assignment.patient
        patients_data.append({
            'id': patient.id,
            'name': patient.get_full_name() or patient.email.split('@')[0],
        })
    
    print("Patients data:", patients_data)  # Debug
    return Response(patients_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_details(request, patient_id):
    """Récupère tous les détails d'un patient pour le modal"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    # Vérifier que le patient est assigné à ce nutritionniste
    is_assigned = PatientAssignment.objects.filter(
        nutritionist=request.user,
        patient_id=patient_id,
        is_active=True
    ).exists()
    
    if not is_assigned:
        return Response({'error': 'Patient not assigned to you'}, status=403)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        patient = User.objects.get(id=patient_id, role='patient')
    except User.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=404)
    
    profile = getattr(patient, 'user_profile', None)
    
    return Response({
        'id': patient.id,
        'full_name': patient.get_full_name(),
        'first_name': patient.first_name,
        'last_name': patient.last_name,
        'email': patient.email,
        'phone': patient.phone,
        'country': patient.country,
        'age': profile.age if profile else 'N/A',
        'weight': profile.weight if profile else 'N/A',
        'height': profile.height if profile else 'N/A',
        'goal_weight': profile.goal if profile else 'N/A',
        'bmi': profile.get_bmi() if profile else 'N/A',
        'bmi_category': profile.get_bmi_category() if profile else 'N/A',
        'health_conditions': profile.health_conditions if profile else [],
        'created_at': patient.date_joined.strftime('%d %B %Y'),
    })

from .models import SpecialOffer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_special_offers(request):
    """Récupère les offres disponibles (diet plans + saisonnières)"""
    
    diet_plans = SpecialOffer.objects.filter(
        is_active=True,
        offer_type='diet_plan'
    ).order_by('-featured', 'price')
    
    seasonal_offers = SpecialOffer.objects.filter(
        is_active=True,
        offer_type='seasonal',
        valid_until__gte=timezone.now().date()
    ).order_by('-featured', '-discount_percent')
    
    return Response({
        'diet_plans': [
            {
                'id': o.id,
                'name': o.name,
                'description': o.description,
                'price': float(o.price),
                'original_price': float(o.original_price) if o.original_price else None,
                'discount_percent': o.discount_percent,
                'image_url': o.image_url,
                'valid_until': o.valid_until.isoformat(),
                'featured': o.featured
            }
            for o in diet_plans
        ],
        'seasonal_offers': [
            {
                'id': o.id,
                'name': o.name,
                'description': o.description,
                'price': float(o.price),
                'original_price': float(o.original_price) if o.original_price else None,
                'discount_percent': o.discount_percent,
                'image_url': o.image_url,
                'valid_until': o.valid_until.isoformat(),
                'days_left': (o.valid_until - timezone.now().date()).days
            }
            for o in seasonal_offers
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def purchase_offer(request, offer_id):
    """Achat d'une offre (diet plan ou saisonnière) avec gestion des options"""
    from django.utils import timezone
    from datetime import timedelta
    from .models import PatientSubscription
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from io import BytesIO
    
    try:
        offer = SpecialOffer.objects.get(id=offer_id, is_active=True)
        patient = request.user
        profile = patient.user_profile
        
        # ============ CORRECTION : IDENTIFIER PREMIUM ============
        # L'offre Premium a l'ID 2 dans votre base de données
        is_premium = (offer_id == 2) or (offer.name and offer.name.lower() == 'premium')
        
        # Récupérer les options du formulaire
        duration_months = request.data.get('duration_months', 1)
        include_ai = request.data.get('include_ai', False)
        include_consultations = request.data.get('include_consultations', False)
        
        # ============ SI PREMIUM, FORCER LES OPTIONS À TRUE ============
        if is_premium:
            include_ai = True
            include_consultations = True
            duration_months = request.data.get('duration_months', 1)  # Garder la durée choisie
        
        duration_days = duration_months * 30
        
        # Vérifier si l'offre saisonnière n'a pas expiré
        if offer.offer_type == 'seasonal' and offer.valid_until < timezone.now().date():
            return Response({'error': 'This offer has expired'}, status=400)
        
        # Désactiver les anciens abonnements actifs
        PatientSubscription.objects.filter(patient=patient, status='active').update(status='expired')
        
        # Désactiver les anciens plans DietPlan
        DietPlan.objects.filter(patient=patient, is_active=True).update(is_active=False)
        
        # Créer le nouvel abonnement
        subscription = PatientSubscription.objects.create(
            patient=patient,
            special_offer=offer,
            plan_name=offer.name,
            price_paid=request.data.get('total_price', offer.price),
            duration_months=duration_months,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=duration_days),
            status='active',
            auto_renew=False
        )
        
        # ============ MISE À JOUR DU PROFIL UTILISATEUR ============
        profile.has_diet_plan = True
        profile.has_ai_tracker = include_ai
        profile.has_consultations = include_consultations
        profile.payment_completed = True
        profile.payment_date = timezone.now()
        
        # Déterminer le type d'abonnement
        if is_premium:
            profile.subscription_plan = 'premium'
        elif include_consultations:
            # Standard + consultations = équivalent Premium pour les fonctionnalités
            profile.subscription_plan = 'premium'
        else:
            profile.subscription_plan = 'standard'
        
        profile.save()
        
        # ============ CRÉER LE PLAN DIET SI NÉCESSAIRE ============
        if offer.offer_type == 'diet_plan':
            nutritionist = None
            if offer.diet_plan and offer.diet_plan.nutritionist:
                nutritionist = offer.diet_plan.nutritionist
            else:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                nutritionist = User.objects.filter(role='nutritionist').first()
            
            new_plan = DietPlan.objects.create(
                nutritionist=nutritionist,
                patient=patient,
                name=offer.name,
                description=offer.description,
                start_date=timezone.now().date(),
                end_date=subscription.end_date,
                is_active=True
            )
            
            if offer.diet_plan:
                for meal in offer.diet_plan.meals.all():
                    Meal.objects.create(
                        plan=new_plan,
                        meal_type=meal.meal_type,
                        food_name=meal.food_name,
                        quantity=meal.quantity,
                        calories=meal.calories,
                        order=meal.order
                    )
        
        # ============ GESTION DES DIFFÉRENTS CAS DE REDIRECTION ============
        
        # CAS 1: PREMIUM - Rediriger vers sélection du nutritionniste
        if is_premium:
            # Sauvegarder en session les infos de la consultation
            request.session['pending_consultation'] = {
                'subscription_id': subscription.id,
                'plan_name': offer.name,
                'duration': duration_months,
                'patient_id': patient.id
            }
            return Response({
                'success': True,
                'message': 'Premium plan activated! Please select your nutritionist.',
                'redirect': '/select-nutritionist/',
                'subscription_plan': 'premium',
                'has_consultations': True,
                'has_ai': True,
                'need_nutritionist': True
            })
        
        # CAS 2: Standard AVEC consultations - Rediriger vers sélection nutritionniste
        elif include_consultations and not is_premium:
            request.session['pending_consultation'] = {
                'subscription_id': subscription.id,
                'plan_name': offer.name,
                'duration': duration_months,
                'patient_id': patient.id
            }
            return Response({
                'success': True,
                'message': 'Plan + Consultations activated! Please select your nutritionist.',
                'redirect': '/select-nutritionist/',
                'subscription_plan': 'premium',
                'has_consultations': True,
                'has_ai': include_ai,
                'need_nutritionist': True
            })
        
        # CAS 3: Standard AVEC AI seulement - Rediriger vers dashboard
        elif include_ai and not include_consultations:
            return Response({
                'success': True,
                'message': f'✅ {offer.name} + AI Tracking activated successfully!',
                'redirect': '/user-profile/',
                'subscription_plan': 'standard',
                'has_ai': True,
                'has_consultations': False
            })
        
        # CAS 4: Standard seul (sans AI ni consultation) - Générer PDF
        else:
            # Générer le PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#27AE60'))
            story.append(Paragraph(f"🍽️ {offer.name}", title_style))
            story.append(Spacer(1, 12))
            story.append(Paragraph(offer.description, styles['Normal']))
            story.append(Spacer(1, 12))
            story.append(Paragraph("<b>What's included:</b>", styles['Heading2']))
            for feature in offer.features:
                story.append(Paragraph(f"✅ {feature}", styles['Normal']))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"<b>Patient:</b> {patient.get_full_name()}", styles['Normal']))
            story.append(Paragraph(f"<b>Email:</b> {patient.email}", styles['Normal']))
            story.append(Paragraph(f"<b>Date:</b> {timezone.now().strftime('%d %B %Y')}", styles['Normal']))
            story.append(Paragraph(f"<b>Valid until:</b> {subscription.end_date.strftime('%d %B %Y')}", styles['Normal']))
            
            doc.build(story)
            buffer.seek(0)
            
            response = HttpResponse(buffer, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="diet_plan_{subscription.id}.pdf"'
            return response
        
    except SpecialOffer.DoesNotExist:
        return Response({'error': 'Offer not found'}, status=404)
    except Exception as e:
        print(f"Purchase offer error: {str(e)}")
        return Response({'error': str(e)}, status=500)
# ==================== ADMIN APPROVAL FUNCTIONS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_offers(request):
    """Admin: Récupère les offres en attente de validation"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    pending_offers = SpecialOffer.objects.filter(
        is_active=False,
        offer_type='diet_plan'
    ).order_by('-submitted_at')
    
    return Response([
        {
            'id': o.id,
            'name': o.name,
            'short_description': o.short_description,
            'description': o.description,
            'price': float(o.price),
            'original_price': float(o.original_price) if o.original_price else None,
            'features': o.features,
            'icon': o.icon,
            'submitted_by': o.submitted_by.get_full_name() if o.submitted_by else 'Unknown',
            'submitted_by_id': o.submitted_by.id if o.submitted_by else None,
            'submitted_at': o.submitted_at.isoformat() if o.submitted_at else None,
        }
        for o in pending_offers
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_offer(request, offer_id):
    """Admin: Approuve une offre et la rend publique"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        offer = SpecialOffer.objects.get(id=offer_id, offer_type='diet_plan')
        
        offer.is_active = True
        offer.save()
        
        # Notification au nutritionniste
        if offer.submitted_by:
            Notification.objects.create(
                nutritionist=offer.submitted_by,
                notification_type='plan_approved',
                title='✅ Your plan has been approved!',
                message=f'Your plan "{offer.name}" has been approved by admin and is now available for purchase.',
                related_id=offer.id
            )
        
        return Response({
            'success': True,
            'message': 'Offer approved and published successfully'
        })
        
    except SpecialOffer.DoesNotExist:
        return Response({'error': 'Offer not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_offer(request, offer_id):
    """Admin: Rejette une offre avec explication"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    explanation = request.data.get('explanation', 'No specific reason provided.')
    
    try:
        offer = SpecialOffer.objects.get(id=offer_id, offer_type='diet_plan')
        
        # Notification au nutritionniste
        if offer.submitted_by:
            Notification.objects.create(
                nutritionist=offer.submitted_by,
                notification_type='plan_rejected',
                title='❌ Your plan was rejected',
                message=f'Your plan "{offer.name}" was rejected. Reason: {explanation}',
                related_id=offer.id
            )
        
        # Option: supprimer ou marquer comme rejeté
        offer.delete()  # ou offer.is_active = False, offer.status = 'rejected'
        
        return Response({
            'success': True,
            'message': 'Offer rejected and nutritionist notified'
        })
        
    except SpecialOffer.DoesNotExist:
        return Response({'error': 'Offer not found'}, status=404)


@api_view(['GET'])
def get_public_diet_plans(request):
    """Récupère tous les plans approuvés pour la page d'accueil"""
    plans = SpecialOffer.objects.filter(
        is_active=True,
        offer_type='diet_plan'
    ).order_by('-featured', 'price')
    
    return Response([
        {
            'id': p.id,
            'name': p.name,
            'short_description': p.short_description or p.description[:80],
            'price': float(p.price),
            'original_price': float(p.original_price) if p.original_price else None,
            'discount_percent': p.discount_percent,
            'features': p.features,
            'icon': p.icon,
            'featured': p.featured,
        }
        for p in plans
    ])

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_seasonal_offer(request):

    """Admin: Crée une offre saisonnière"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    data = request.data
    
    try:
        offer = SpecialOffer.objects.create(
            name=data['name'],
            short_description=data.get('short_description', ''),
            description=data.get('description', ''),
            price=data['price'],
            original_price=data.get('original_price'),
            discount_percent=data.get('discount_percent', 0),
            features=data.get('features', []),
            icon=data.get('icon', '🌙'),
            offer_type='seasonal',
            valid_until=data['valid_until'],
            is_active=True,
            featured=data.get('featured', False)
        )
        
        return Response({
            'success': True,
            'message': 'Seasonal offer created successfully',
            'offer_id': offer.id
        }, status=201)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_consultation_requests(request):
    """Récupère les demandes de consultation en attente"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    # Récupère les consultations en attente (pending) pour ce nutritionniste
    requests = Consultation.objects.filter(
        nutritionist=request.user,
        status='pending'
    ).select_related('patient')
    
    return Response([
        {
            'id': c.id,
            'patient_name': c.patient.get_full_name() or c.patient.email,
            'patient_email': c.patient.email,
            'date': c.date.isoformat(),
            'date_display': c.date.strftime('%b %d, %Y • %I:%M %p'),
            'notes': c.notes or f"Trial consultation requested by {c.patient.email}",
            'created_at': c.created_at.isoformat(),
        }
        for c in requests
    ])

# ==================== ASSIGNMENT REQUESTS (Admin Approval Workflow) ====================
from .models import AssignmentRequest
from django.contrib.auth import get_user_model
User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_requests(request):
    """Admin - Récupère les demandes d'assignation en attente"""
    if not request.user.is_superuser and request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    # Récupérer les demandes en attente
    requests = AssignmentRequest.objects.filter(status='pending').select_related('patient', 'nutritionist').order_by('-created_at')
    
    return Response({
        'requests': [
            {
                'id': r.id,
                'patient_id': r.patient.id,
                'patient_name': r.patient.get_full_name() or r.patient.email.split('@')[0],
                'patient_email': r.patient.email,
                'requested_nutritionist_id': r.nutritionist.id,
                'requested_nutritionist_name': r.nutritionist.get_full_name() or r.nutritionist.email.split('@')[0],
                'order_data': getattr(r, 'order_data', {}),
                'created_at': r.created_at.isoformat(),
                'created_at_display': r.created_at.strftime('%d %b %Y, %H:%M')
            }
            for r in requests
        ]
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_assignment_request(request, request_id):
    """Admin - Accepte ou refuse une demande d'assignation"""
    if not request.user.is_superuser and request.user.role != 'admin':
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        assignment_request = AssignmentRequest.objects.get(id=request_id, status='pending')
    except AssignmentRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=404)
    
    action = request.data.get('action')  # 'approve' or 'reject'
    alternative_nutritionist_id = request.data.get('alternative_nutritionist_id')
    reason = request.data.get('reason', '')
    
    if action == 'approve':
        # Déterminer quel nutritionniste assigner
        if alternative_nutritionist_id and alternative_nutritionist_id != '':
            try:
                nutritionist = User.objects.get(id=alternative_nutritionist_id, role='nutritionist')
            except User.DoesNotExist:
                return Response({'error': 'Alternative nutritionist not found'}, status=404)
        else:
            nutritionist = assignment_request.nutritionist
        
        # Désactiver les anciennes assignations
        PatientAssignment.objects.filter(patient=assignment_request.patient, is_active=True).update(is_active=False)
        
        # Créer la nouvelle assignation
        PatientAssignment.objects.create(
            patient=assignment_request.patient,
            nutritionist=nutritionist,
            is_active=True
        )
        
        # Mettre à jour le profil du patient
        profile = assignment_request.patient.user_profile
        if profile:
            profile.has_consultations = True
            profile.has_diet_plan = True
            profile.payment_completed = True
            if hasattr(assignment_request, 'order_data') and assignment_request.order_data:
                plan_name = assignment_request.order_data.get('planName', 'premium')
                profile.subscription_plan = plan_name.lower()
            else:
                profile.subscription_plan = 'premium'
            profile.save()
        
        assignment_request.status = 'approved'
        assignment_request.save()
        
        # 🔔 NOTIFICATION POUR LE PATIENT
        Notification.objects.create(
            user=assignment_request.patient,
            notification_type='assignment_approved',
            title='✅ Nutritionist Assigned!',
            message=f'Your request has been approved. You are now assigned to {nutritionist.get_full_name() or nutritionist.email}. You can now send messages and book consultations.',
            related_id=nutritionist.id,
            is_read=False
        )
        
        # 🔔 NOTIFICATION POUR LE NUTRITIONNISTE
        Notification.objects.create(
            nutritionist=nutritionist,
            notification_type='new_patient_assigned',
            title='👤 New Patient Assigned',
            message=f'{assignment_request.patient.get_full_name() or assignment_request.patient.email} has been assigned to you by admin.',
            related_patient=assignment_request.patient,
            related_id=assignment_request.patient.id,
            is_read=False
        )
        
        return Response({
            'success': True, 
            'message': f'Request approved! {nutritionist.get_full_name()} assigned to patient.',
            'assigned_nutritionist': nutritionist.get_full_name()
        })
    
    elif action == 'reject':
        assignment_request.status = 'rejected'
        assignment_request.rejection_reason = reason
        assignment_request.save()
        
        # 🔔 NOTIFICATION POUR LE PATIENT
        Notification.objects.create(
            user=assignment_request.patient,
            notification_type='assignment_rejected',
            title='❌ Nutritionist Request Update',
            message=f'Your request for {assignment_request.nutritionist.get_full_name()} was not approved. Reason: {reason}. Please contact support for assistance or try another nutritionist.',
            related_id=assignment_request.id,
            is_read=False
        )
        
        return Response({
            'success': True, 
            'message': 'Request rejected. Patient has been notified.'
        })
    
    return Response({'error': 'Invalid action'}, status=400)

    
def get_time_ago(dt):
    """Calcule le temps écoulé depuis une date"""
    from django.utils import timezone
    now = timezone.now()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return 'Yesterday'
        return f'{diff.days} days ago'
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f'{hours} hours ago'
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f'{minutes} minutes ago'
    else:
        return 'Just now'
