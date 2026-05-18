from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserProfile, WeightHistory
from datetime import date
from django.views.decorators.csrf import csrf_exempt 
from django.utils import timezone


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@csrf_exempt 
def get_profile_stats(request):
    """Récupère toutes les stats pour le dashboard"""
    profile = request.user.user_profile
    user = request.user
    # Récupérer les 6 dernières entrées de poids
    weight_history = WeightHistory.objects.filter(user=request.user).order_by('-date')[:6]
    
    # Formater pour le frontend (ordre chronologique)
    timeline = []
    for entry in reversed(weight_history):
        timeline.append({
            'date': entry.date.strftime('%b %d'),
            'weight': entry.weight_kg,
            'bmi': round(entry.weight_kg / ((profile.height / 100) ** 2), 1)
        })
    
    # Si pas d'historique, utiliser le poids actuel
    if not timeline:
        current_bmi = profile.get_bmi()
        timeline.append({
            'date': date.today().strftime('%b %d'),
            'weight': profile.weight,
            'bmi': current_bmi
        })

     # Calculer la variation de poids (dernier poids - avant-dernier)
    weight_change = 0
    if weight_history.count() >= 2:
        # Le premier est le plus récent
        latest = weight_history.first()
        previous = weight_history[1]
        weight_change = round(latest.weight_kg - previous.weight_kg, 1)
    
    
    return Response({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'streak': profile.nutrition_streak,
        'health_score': profile.get_health_score(),
        'bmi': profile.get_bmi(),
        'bmi_category': profile.get_bmi_category(),
         'height'  : profile.height,
         'current_weight': profile.weight,
         'goal': profile.goal,        # ← AJOUTE
        'health_conditions': profile.health_conditions if hasattr(profile, 'health_conditions') else [], 
        'weight_change': weight_change,  # À calculer si tu as l'historique
        'timeline': timeline
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_weight(request):
    """Met à jour le poids et crée une entrée dans l'historique"""
    new_weight = request.data.get('weight')
    
    if not new_weight:
        return Response({'error': 'Weight required'}, status=400)
    
    profile = request.user.user_profile
    
    # Sauvegarder l'ancien poids dans l'historique
    WeightHistory.objects.create(
        user=request.user,
        weight_kg=profile.weight
    )
    
    # Mettre à jour le poids actuel
    profile.weight = float(new_weight)
    profile.save()
    
    return Response({
        'message': 'Weight updated',
        'new_bmi': profile.get_bmi(),
        'new_bmi_category': profile.get_bmi_category(),
        'health_score': profile.get_health_score()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_streak(request):
    """Met à jour le streak (appelé quand l'utilisateur valide sa journée)"""
    from datetime import date, timedelta
    
    profile = request.user.user_profile
    today = date.today()
    
    # Vérifier si déjà validé aujourd'hui
    if profile.last_streak_date == today:
        return Response({'streak': profile.nutrition_streak, 'already': True})
    
    # Si hier a été validé, incrémenter, sinon recommencer
    if profile.last_streak_date == today - timedelta(days=1):
        profile.nutrition_streak += 1
    else:
        profile.nutrition_streak = 1
    
    profile.last_streak_date = today
    profile.save()
    
    return Response({'streak': profile.nutrition_streak})



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_weight_history(request):
    """Récupère l'historique des poids pour le graphique"""
    weight_history = WeightHistory.objects.filter(user=request.user).order_by('date')[:30]
    
    # Récupérer l'objectif de poids
    goal_weight = request.user.user_profile.goal if hasattr(request.user.user_profile, 'goal') else None

    
    return Response({
        'labels': [entry.date.strftime('%d/%m') for entry in weight_history],
        'weights': [entry.weight_kg for entry in weight_history],
        'goal_weight': goal_weight,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_achievements(request):
    """Calcule les achievements du patient"""
    try:
        profile = request.user.user_profile
        streak = profile.nutrition_streak if profile.nutrition_streak else 0
        
        # Compter les consultations complétées
        consultations_count = 0
        try:
            from consultations.models import Consultation
            consultations_count = Consultation.objects.filter(
                patient=request.user,  # ← CORRIGÉ : 'patient' au lieu de 'user'
                status='completed'
            ).count()
        except:
            consultations_count = 0
        
        achievements = [
            {
                'icon': '🔥' if streak >= 7 else '⏳',
                'text': f'{streak}-day streak tracking meals',
                'completed': streak >= 7,
                'progress': f'{streak}/7' if streak < 7 else None
            },
            {
                'icon': '✅' if consultations_count >= 1 else '📅',
                'text': 'Complete your first consultation',
                'completed': consultations_count >= 1,
                'progress': None
            },
            {
                'icon': '🏅',
                'text': 'Walked 8k steps avg last week',
                'completed': False,
                'progress': '5.2k/8k'
            }
        ]
        
        return Response({
            'streak': streak,
            'consultations_count': consultations_count,
            'achievements': achievements,
        })
    except Exception as e:
        print("Erreur dans get_achievements:", str(e))
        return Response({
            'streak': 0,
            'consultations_count': 0,
            'achievements': [
                {'icon': '⏳', 'text': 'Start tracking your progress', 'completed': False}
            ]
        }, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_weekly_report(request):
    """Récupère le dernier rapport du nutritionniste"""
    from consultations.models import WeeklyReport
    latest_report = WeeklyReport.objects.filter(
        patient=request.user
    ).order_by('-created_at').first()
    
    if latest_report:
        return Response({
            'has_report': True,
            'content': latest_report.content,
            'nutritionist_name': latest_report.nutritionist.get_full_name(),
            'date': latest_report.created_at.strftime('%d %B %Y'),
        })
    else:
        return Response({
            'has_report': False,
            'message': 'No weekly report yet. Your nutritionist will provide feedback soon.'
        })
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_calendar(request):
    """Récupère les consultations + repas du diet plan pour le calendrier"""
    from consultations.models import Consultation
    from nutritionists.models import PatientMealChecklist
    from django.utils import timezone
    
    consultations = Consultation.objects.filter(
        patient=request.user,
        status='confirmed',
        date__gte=timezone.now().date()
    ).order_by('date')
    
    # Récupérer les repas à venir (checklist)
    meals = PatientMealChecklist.objects.filter(
        patient=request.user,
        status='pending',
        date__gte=timezone.now().date()
    ).order_by('date')[:30]
    
    # Grouper les repas par date
    meals_by_date = {}
    for meal in meals:
        date_str = meal.date.isoformat()
        if date_str not in meals_by_date:
            meals_by_date[date_str] = []
        meals_by_date[date_str].append({
            'name': meal.meal_name,
            'time': meal.meal_time if hasattr(meal, 'meal_time') else '12:00',
        })
    
    return Response({
        'consultations': [
            {
                'id': c.id,
                'type': 'consultation',
                'nutritionist_name': c.nutritionist.get_full_name() or c.nutritionist.email.split('@')[0],
                'date': c.date.isoformat(),
                'zoom_link': c.zoom_link,
            }
            for c in consultations
        ],
        'meals': [
            {
                'type': 'meal',
                'date': date,
                'meals': meals_list
            }
            for date, meals_list in meals_by_date.items()
        ]
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_diet_plan(request):
    """Récupère le plan alimentaire actif du patient"""
    from nutritionists.models import DietPlan
    
    plan = DietPlan.objects.filter(
        patient=request.user,
        is_active=True
    ).first()
    
    if not plan:
        return Response({'has_plan': False, 'message': 'No active diet plan'})
    
    meals_by_type = {}
    for meal in plan.meals.all():
        if meal.meal_type not in meals_by_type:
            meals_by_type[meal.meal_type] = []
        meals_by_type[meal.meal_type].append({
            'id': meal.id,
            'food_name': meal.food_name,
            'quantity': meal.quantity,
            'calories': meal.calories,
            'meal_type': meal.meal_type,
        })
    
    return Response({
        'has_plan': True,
        'plan': {
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'start_date': plan.start_date,
            'end_date': plan.end_date,
            'nutritionist': plan.nutritionist.get_full_name(),
            'meals': meals_by_type,
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_today_meals_checklist(request):
    """Récupère les repas du jour du patient"""
    from nutritionists.models import PatientMealChecklist
    from django.utils import timezone
    
    today = timezone.now().date()
    meals = PatientMealChecklist.objects.filter(
        patient=request.user,
        date=today
    ).order_by('meal_time')
    
    return Response({
        'date': today,
        'meals': [
            {
                'id': m.id,
                'name': m.meal_name,
                'status': m.status,
                'meal_time': m.meal_time,
            }
            for m in meals
        ],
        'completed_count': meals.filter(status='completed').count(),
        'total_count': meals.count()
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_meal_checklist(request, checklist_id):
    """Marque un repas comme complété"""
    from nutritionists.models import PatientMealChecklist
    from django.utils import timezone
    
    try:
        checklist = PatientMealChecklist.objects.get(id=checklist_id, patient=request.user)
        checklist.status = 'completed'
        checklist.completed_at = timezone.now()
        checklist.save()
        
        # Vérifier si tous les repas du jour sont complétés
        today = timezone.now().date()
        all_meals = PatientMealChecklist.objects.filter(patient=request.user, date=today)
        completed = all_meals.filter(status='completed').count()
        
        # Optionnel: mettre à jour le streak
        if completed == all_meals.count() and all_meals.count() > 0:
            from users.models import UserProfile
            profile = request.user.user_profile
            from datetime import date, timedelta
            if profile.last_streak_date == today - timedelta(days=1):
                profile.nutrition_streak += 1
            elif profile.last_streak_date != today:
                profile.nutrition_streak = 1
            profile.last_streak_date = today
            profile.save()
        
        return Response({'status': 'completed', 'message': 'Meal marked as completed'})
    except PatientMealChecklist.DoesNotExist:
        return Response({'error': 'Meal not found'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_payment(request):
    """Valide le paiement et active le plan choisi"""
    from django.utils import timezone
    
    plan = request.data.get('plan', 'standard')
    profile = request.user.user_profile
    
    profile.subscription_plan = plan
    profile.payment_completed = True
    profile.payment_date = timezone.now()
    profile.save()
    
    # Assigner automatiquement un nutritionniste pour le premium
    if plan == 'premium':
        from nutritionists.models import PatientAssignment
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Chercher un nutritionniste disponible
        nutritionist = User.objects.filter(role='nutritionist').first()
        if nutritionist:
            PatientAssignment.objects.get_or_create(
                patient=request.user,
                nutritionist=nutritionist,
                defaults={'is_active': True}
            )
    
    return Response({
        'success': True, 
        'message': f'Payment successful! {plan.capitalize()} plan activated.',
        'redirect': '/user-profile/'
    })

from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response




@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_view(request):
    """Affiche la page de paiement ou traite le paiement"""
    profile = request.user.user_profile
    
    if request.method == 'GET':
        # Retourner les infos du plan actuel
        return Response({
            'current_plan': getattr(profile, 'subscription_plan', 'free'),
            'payment_completed': getattr(profile, 'payment_completed', False)
        })
    
    elif request.method == 'POST':
        plan = request.data.get('plan', 'standard')
        
        # Simuler un paiement (toujours réussi en demo)
        profile.subscription_plan = plan
        profile.payment_completed = True
        profile.payment_date = timezone.now()
        profile.save()
        
        # Pour le plan premium, assigner un nutritionniste
        if plan == 'premium':
            from nutritionists.models import PatientAssignment
            # Utiliser get_user_model() au lieu de User directement
            UserModel = get_user_model()
            nutritionist = UserModel.objects.filter(role='nutritionist').first()
            if nutritionist:
                PatientAssignment.objects.get_or_create(
                    patient=request.user,
                    nutritionist=nutritionist,
                    defaults={'is_active': True}
                )
        
        return Response({
            'success': True,
            'message': f'✅ {plan.capitalize()} plan activated!',
            'redirect': '/dashboard/'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_plan(request):

    """Récupère le plan de l'utilisateur"""
    profile = request.user.user_profile
    
    subscription_plan = getattr(profile, 'subscription_plan', 'free')
    payment_completed = getattr(profile, 'payment_completed', False)
    
    return Response({
        'subscription_plan': subscription_plan,
        'payment_completed': payment_completed,
        'has_consultations': subscription_plan == 'premium',
        'has_messages': subscription_plan == 'premium',
        'has_diet_plan': subscription_plan in ['standard', 'premium'],
        'has_ai': subscription_plan in ['standard', 'premium'],
        'has_progress': subscription_plan in ['standard', 'premium']
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription_status(request):

    """Vérifie si l'utilisateur a un abonnement actif"""
    from nutritionists.models import PatientSubscription
    from django.utils import timezone
    
    user = request.user
    
    # Mettre à jour les abonnements expirés
    expired_subs = PatientSubscription.objects.filter(
        patient=user,
        status='active',
        end_date__lt=timezone.now().date()
    )
    expired_count = expired_subs.update(status='expired')
    
    # Récupérer l'abonnement actif
    current_subscription = PatientSubscription.objects.filter(
        patient=user,
        status='active',
        end_date__gte=timezone.now().date()
    ).first()
    
    has_active_subscription = current_subscription is not None
    
    return Response({
        'has_active_subscription': has_active_subscription,
        'subscription': {
            'plan_name': current_subscription.plan_name if current_subscription else None,
            'start_date': current_subscription.start_date.isoformat() if current_subscription else None,
            'end_date': current_subscription.end_date.isoformat() if current_subscription else None,
            'days_left': current_subscription.days_left if current_subscription else 0,
            'is_expiring_soon': current_subscription.is_expiring_soon if current_subscription else False
        } if current_subscription else None,
        'expired_subscriptions_count': expired_count
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invoices(request):
    """Récupère les factures/abonnements de l'utilisateur connecté"""
    from nutritionists.models import PatientSubscription
    from django.utils import timezone
    
    subscriptions = PatientSubscription.objects.filter(
        patient=request.user
    ).order_by('-created_at')
    
    # Calculer le montant total dépensé
    total_spent = sum(float(s.price_paid) for s in subscriptions)
    
    # Récupérer le dernier paiement
    last_payment = subscriptions.first()
    
    return Response({
        'subscriptions': [
            {
                'id': s.id,
                'plan_name': s.plan_name,
                'amount': float(s.price_paid),
                'duration_months': s.duration_months,
                'start_date': s.start_date.isoformat(),
                'end_date': s.end_date.isoformat(),
                'status': s.status,
                'is_active': s.is_active,
                'days_left': s.days_left,
                'created_at': s.created_at.isoformat(),
                'payment_date': s.created_at.strftime('%d %B %Y'),
                'expiry_date': s.end_date.strftime('%d %B %Y')
            }
            for s in subscriptions
        ],
        'summary': {
            'total_spent': total_spent,
            'active_subscriptions': sum(1 for s in subscriptions if s.is_active),
            'total_subscriptions': subscriptions.count(),
            'last_payment': {
                'date': last_payment.created_at.strftime('%d %B %Y') if last_payment else None,
                'amount': float(last_payment.price_paid) if last_payment else None,
                'plan': last_payment.plan_name if last_payment else None
            } if last_payment else None
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_subscription_status(request):

    """Vérifie si l'utilisateur a un abonnement actif"""
    from nutritionists.models import PatientSubscription
    from django.utils import timezone
    
    user = request.user
    
    # Mettre à jour les abonnements expirés
    expired_subs = PatientSubscription.objects.filter(
        patient=user,
        status='active',
        end_date__lt=timezone.now().date()
    )
    expired_count = expired_subs.update(status='expired')
    
    # Récupérer l'abonnement actif
    current_subscription = PatientSubscription.objects.filter(
        patient=user,
        status='active',
        end_date__gte=timezone.now().date()
    ).first()
    
    has_active_subscription = current_subscription is not None
    
    return Response({
        'has_active_subscription': has_active_subscription,
        'subscription': {
            'plan_name': current_subscription.plan_name if current_subscription else None,
            'start_date': current_subscription.start_date.isoformat() if current_subscription else None,
            'end_date': current_subscription.end_date.isoformat() if current_subscription else None,
            'days_left': current_subscription.days_left if current_subscription else 0,
            'is_expiring_soon': current_subscription.is_expiring_soon if current_subscription else False
        } if current_subscription else None,
        'expired_subscriptions_count': expired_count
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_features(request):
    """Récupère les features disponibles pour l'utilisateur selon son achat"""
    profile = request.user.user_profile
    
    # Récupérer les attributs avec valeurs par défaut
    has_diet_plan = getattr(profile, 'has_diet_plan', True)  # True si paiement effectué
    has_ai_tracker = getattr(profile, 'has_ai_tracker', False)
    has_consultations = getattr(profile, 'has_consultations', False)
    subscription_plan = getattr(profile, 'subscription_plan', 'standard')
    
    return Response({
        'has_diet_plan': has_diet_plan,
        'has_ai_tracker': has_ai_tracker,
        'has_consultations': has_consultations,
        'subscription_plan': subscription_plan,
        'has_messages': has_consultations,  # Les messages sont liés aux consultations
        'has_progress': has_diet_plan,
        'has_calendar': has_diet_plan
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_plan_pdf(request, subscription_id):
    """Télécharge le PDF du plan alimentaire"""
    from nutritionists.models import PatientSubscription, SpecialOffer
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from io import BytesIO
    
    try:
        subscription = PatientSubscription.objects.get(id=subscription_id, patient=request.user)
        offer = subscription.special_offer
        
        # Créer le PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Style personnalisé
        title_style = ParagraphStyle(
            'CustomTitle', 
            parent=styles['Heading1'], 
            fontSize=24, 
            textColor=colors.HexColor('#27AE60')
        )
        
        # Contenu du PDF
        story.append(Paragraph(f"🍽️ {offer.name}", title_style))
        story.append(Spacer(1, 12))
        story.append(Paragraph(offer.description, styles['Normal']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>What's included:</b>", styles['Heading2']))
        
        for feature in offer.features:
            story.append(Paragraph(f"✅ {feature}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<b>Patient:</b> {request.user.get_full_name()}", styles['Normal']))
        story.append(Paragraph(f"<b>Email:</b> {request.user.email}", styles['Normal']))
        story.append(Paragraph(f"<b>Date:</b> {timezone.now().strftime('%d %B %Y')}", styles['Normal']))
        story.append(Paragraph(f"<b>Valid until:</b> {subscription.end_date.strftime('%d %B %Y')}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        
        # Marquer comme téléchargé
        profile = request.user.user_profile
        profile.downloaded_plan_pdf = True
        profile.save()
        
        # Retourner le PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="diet_plan_{subscription.id}.pdf"'
        return response
        
    except PatientSubscription.DoesNotExist:
        return Response({'error': 'Subscription not found'}, status=404)
    


from .models import Message
from nutritionists.models import Notification
from django.contrib.auth import get_user_model

User = get_user_model()



from nutritionists.models import PatientAssignment

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversations(request):
    """Récupère la liste des conversations pour l'utilisateur connecté"""
    user = request.user
    
    conversations = []
    
    if user.role == 'nutritionist':
        # Pour un nutritionniste : uniquement ses patients assignés
        assigned_patients = PatientAssignment.objects.filter(
            nutritionist=user,
            is_active=True
        ).select_related('patient')
        
        for assignment in assigned_patients:
            patient = assignment.patient
            
            # Vérifier s'il y a des messages échangés
            last_message = Message.objects.filter(
                sender__in=[user.id, patient.id],
                receiver__in=[user.id, patient.id]
            ).order_by('-created_at').first()
            
            unread_count = Message.objects.filter(
                sender=patient,
                receiver=user,
                is_read=False
            ).count()
            
            conversations.append({
                'user_id': patient.id,
                'name': patient.get_full_name() or patient.email.split('@')[0],
                'email': patient.email,
                'avatar': patient.first_name[0] if patient.first_name else 'P',
                'role': 'patient',
                'last_message': last_message.content if last_message else 'No messages yet',
                'last_message_time': last_message.created_at.isoformat() if last_message else None,
                'unread_count': unread_count
            })
    
    else:
        # Pour un patient : uniquement son nutritionniste assigné
        assignment = PatientAssignment.objects.filter(
            patient=user,
            is_active=True
        ).select_related('nutritionist').first()
        
        if assignment:
            nutritionist = assignment.nutritionist
            
            last_message = Message.objects.filter(
                sender__in=[user.id, nutritionist.id],
                receiver__in=[user.id, nutritionist.id]
            ).order_by('-created_at').first()
            
            unread_count = Message.objects.filter(
                sender=nutritionist,
                receiver=user,
                is_read=False
            ).count()
            
            conversations.append({
                'user_id': nutritionist.id,
                'name': nutritionist.get_full_name() or nutritionist.email.split('@')[0],
                'email': nutritionist.email,
                'avatar': nutritionist.first_name[0] if nutritionist.first_name else 'N',
                'role': 'nutritionist',
                'last_message': last_message.content if last_message else 'No messages yet',
                'last_message_time': last_message.created_at.isoformat() if last_message else None,
                'unread_count': unread_count
            })
    
    # Trier par date du dernier message
    conversations.sort(key=lambda x: x['last_message_time'] or '', reverse=True)
    return Response(conversations)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages(request, user_id):
    """Récupère les messages entre l'utilisateur connecté et un autre utilisateur"""
    user = request.user
    
    messages = Message.objects.filter(
        sender__in=[user.id, user_id],
        receiver__in=[user.id, user_id]
    ).order_by('created_at')
    
    # Marquer les messages reçus comme lus
    Message.objects.filter(
        sender_id=user_id,
        receiver=user,
        is_read=False
    ).update(is_read=True)
    
    return Response([
        {
            'id': m.id,
            'sender_id': m.sender.id,
            'sender_name': m.sender.get_full_name() or m.sender.email.split('@')[0],
            'sender_role': m.sender.role,
            'content': m.content,
            'created_at': m.created_at.isoformat(),
            'time_display': m.created_at.strftime('%H:%M - %d/%m/%Y'),
            'is_mine': m.sender.id == user.id
        }
        for m in messages
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """Envoie un message à un autre utilisateur"""
    receiver_id = request.data.get('receiver_id')
    content = request.data.get('content', '').strip()
    
    if not receiver_id or not content:
        return Response({'error': 'Missing required fields'}, status=400)
    
    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    
    message = Message.objects.create(
        sender=request.user,
        receiver=receiver,
        content=content
    )
    
    # Créer une notification pour le destinataire
    if receiver.role == 'nutritionist':
        Notification.objects.create(
            nutritionist=receiver,
            notification_type='new_message',
            title='💬 New Message',
            message=f'{request.user.get_full_name() or request.user.email} sent you a message.',
            related_patient=request.user,
            related_id=message.id,
            is_read=False
        )
    else:
        # Pour les patients, créer une notification (à adapter selon ton modèle)
        # Si tu as un modèle Notification pour les patients
        pass
    
    return Response({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'created_at': message.created_at.isoformat(),
            'time_display': message.created_at.strftime('%H:%M - %d/%m/%Y'),
            'is_mine': True
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_nutritionist(request):
    user = request.user
    
    if user.role != 'patient':
        return Response({'error': 'Only patients can access this'}, status=403)
    
    from nutritionists.models import PatientAssignment
    
    assignment = PatientAssignment.objects.filter(
        patient=user,
        is_active=True
    ).select_related('nutritionist').first()
    
    if not assignment or not assignment.nutritionist:
        return Response({'error': 'No nutritionist assigned'}, status=404)
    
    nutritionist = assignment.nutritionist
    
    return Response({
        'id': nutritionist.id,
        'name': nutritionist.get_full_name() or nutritionist.email.split('@')[0],
        'email': nutritionist.email,
        'phone': getattr(nutritionist, 'phone', ''),
        'specialization': getattr(nutritionist, 'specialization', 'Nutritionist'),
        'is_available': True,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_nutritionist(request):
    """Patient demande un nutritionniste (créé une demande admin)"""
    from nutritionists.models import AssignmentRequest, PatientAssignment
    from nutritionists.models import Notification
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        nutritionist_id = request.data.get('nutritionist_id')
        
        if not nutritionist_id:
            return Response({'error': 'Nutritionist ID required'}, status=400)
        
        if request.user.role != 'patient':
            return Response({'error': 'Only patients can request a nutritionist'}, status=403)
        
        try:
            nutritionist = User.objects.get(id=nutritionist_id, role='nutritionist')
        except User.DoesNotExist:
            return Response({'error': 'Nutritionist not found'}, status=404)
        
        # Vérifier si une demande existe déjà en attente
        existing_request = AssignmentRequest.objects.filter(
            patient=request.user,
            nutritionist=nutritionist,
            status='pending'
        ).first()
        
        if existing_request:
            # Si une demande existe déjà, rediriger directement vers le dashboard
            return Response({
                'success': True,
                'message': 'Your request is already pending. You will be notified once approved.',
                'already_pending': True,
                'redirect': '/user-profile/'
            })
        
        # Vérifier si déjà assigné
        existing_assign = PatientAssignment.objects.filter(
            patient=request.user,
            nutritionist=nutritionist,
            is_active=True
        ).first()
        
        if existing_assign:
            return Response({
                'success': True,
                'message': f'You are already assigned to {nutritionist.get_full_name()}.',
                'already_assigned': True,
                'redirect': '/user-profile/'
            })
        
        # Créer la demande
        assignment_request = AssignmentRequest.objects.create(
            patient=request.user,
            nutritionist=nutritionist,
            status='pending'
        )
        
        # 🔔 NOTIFICATION POUR L'ADMIN (via admin_dashboard)
        from admin_dashboard.views import create_admin_notification
        Notification.objects.create(
            nutritionist=None,
            notification_type='assignment_request',
            title='🔔 New Assignment Request',
            message=f'{request.user.get_full_name() or request.user.email} wants to be assigned to {nutritionist.get_full_name() or nutritionist.email}.',
            related_patient=request.user,
            related_id=assignment_request.id,
            is_read=False,
            is_admin_notification=True
        )
        
        # L'utilisateur a accès au dashboard même avant confirmation
        # On ne bloque pas l'accès, on l'envoie au dashboard
        return Response({
            'success': True,
            'message': 'Your request has been sent to admin. You will be notified once approved. You can continue using the dashboard while waiting.',
            'request_id': assignment_request.id,
            'redirect': '/user-profile/'
        })
        
    except Exception as e:
        logger.error(f"Error in assign_nutritionist: {str(e)}")
        return Response({'error': str(e)}, status=500)