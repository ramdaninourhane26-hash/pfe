from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from users.models import UserProfile
from nutritionists.models import PatientAssignment, Notification
from consultations.models import NutritionistProfile 


User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    """Récupère tous les utilisateurs pour l'admin"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    users = User.objects.filter(role='patient').order_by('-date_joined')
    
    users_data = []
    for user in users:
        profile = getattr(user, 'user_profile', None)

        assignment = PatientAssignment.objects.filter(
            patient=user,
            is_active=True
        ).select_related('nutritionist').first()
        
        users_data.append({
            'id': user.id,
            'name': user.get_full_name() or user.email.split('@')[0],
            'email': user.email,
            'role': user.role,
            'plan': 'Active' if user.is_active else 'Inactive',
            'status': 'Active' if user.is_active else 'Blocked',
            'weight': profile.weight if profile else None,
            'height': profile.height if profile else None,
            'goal_weight': profile.goal if profile else None,
            'health_conditions': profile.health_conditions if profile else [],
            'created_at': user.date_joined,
             'assigned_nutritionist_id': assignment.nutritionist.id if assignment else None,
            'assigned_nutritionist_name': assignment.nutritionist.get_full_name() if assignment else None,

        })
    
    return Response(users_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionists_list(request):
    """Récupère la liste des nutritionnistes pour l'assignation"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    nutritionists = User.objects.filter(role='nutritionist')
    
    return Response([
        {
            'id': n.id,
            'name': n.get_full_name() or n.email.split('@')[0],
            'email': n.email,
        }
        for n in nutritionists
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_patient_to_nutritionist(request):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    patient_id = request.data.get('patient_id')
    nutritionist_id = request.data.get('nutritionist_id')
    
    if not patient_id or not nutritionist_id:
        return Response({'error': 'Patient and nutritionist required'}, status=400)
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    from nutritionists.models import PatientAssignment, Notification
    
    try:
        patient = User.objects.get(id=patient_id, role='patient')
    except User.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=404)
    
    try:
        nutritionist = User.objects.get(id=nutritionist_id, role='nutritionist')
    except User.DoesNotExist:
        return Response({'error': 'Nutritionist not found'}, status=404)
    
    assignment, created = PatientAssignment.objects.get_or_create(
        patient=patient,
        nutritionist=nutritionist,
        defaults={'is_active': True}
    )
    
    if not created and not assignment.is_active:
        assignment.is_active = True
        assignment.save()
    
    # ← CRÉATION DE LA NOTIFICATION
    Notification.objects.create(
        nutritionist=nutritionist,
        notification_type='patient_assigned',
        title='New Patient Assigned 🎉',
        message=f'{patient.get_full_name()} has been assigned to you. Check your patient list!',
        related_patient=patient,
    )
    
    return Response({'message': f'Patient {patient.email} assigned to {nutritionist.email}'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def block_user(request, user_id):
    """Bloque ou active un utilisateur"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        status_text = 'blocked' if not user.is_active else 'activated'
        return Response({'message': f'User {user.email} {status_text}'})
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_patient(request):
    """Crée un nouveau patient (admin seulement)"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    data = request.data
    
    # Vérifier si l'email existe déjà
    if User.objects.filter(email=data['email']).exists():
        return Response({'error': 'Email already exists'}, status=400)
    
    # Créer l'utilisateur
    patient = User.objects.create_user(
        email=data['email'],
        password=data['password'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        role='patient'
    )
    
    # Créer le profil
    from users.models import UserProfile
    UserProfile.objects.create(
        user=patient,
        weight=data.get('weight', 0),
        height=data.get('height', 0),
        goal_weight_kg=data.get('goal_weight'),
        health_conditions=data.get('health_conditions', [])
    )
    
    return Response({
        'message': f'Patient {patient.email} created successfully',
        'patient_id': patient.id
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_nutritionists(request):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    from nutritionists.models import PatientAssignment
    from consultations.models import NutritionistProfile
    
    nutritionists = User.objects.filter(role='nutritionist').order_by('-date_joined')
    
    nutritionists_data = []
    for nutritionist in nutritionists:
        # Récupérer le profil
        try:
            profile = NutritionistProfile.objects.get(user=nutritionist)
            specialization = profile.specialization if profile.specialization else 'Not specified'
        except NutritionistProfile.DoesNotExist:
            specialization = 'No profile'
        
        # Compter les patients assignés
        patients_count = PatientAssignment.objects.filter(
            nutritionist=nutritionist,
            is_active=True
        ).count()
        
        nutritionists_data.append({
            'id': nutritionist.id,
            'name': nutritionist.get_full_name() or nutritionist.email.split('@')[0],
            'email': nutritionist.email,
            'specialization': specialization,
            'patients_count': patients_count,
            'status': 'Active' if nutritionist.is_active else 'Inactive',
        })
    
    return Response(nutritionists_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_nutritionist(request):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    data = request.data
    
    if User.objects.filter(email=data['email']).exists():
        return Response({'error': 'Email already exists'}, status=400)
    
    nutritionist = User.objects.create_user(
        email=data['email'],
        password=data['password'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        role='nutritionist',
        is_staff=True
    )
    
    # Créer le profil nutritionniste
    from consultations.models import NutritionistProfile
    NutritionistProfile.objects.create(
        user=nutritionist,
        specialization=data.get('specialization', ''),
        bio=data.get('bio', ''),
        experience_years=data.get('experience_years', 0),
        is_available=data.get('is_available', True)
    )
    
    return Response({'message': f'Nutritionist {nutritionist.email} created successfully'}, status=201)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_nutritionist_status(request, nutritionist_id):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        nutritionist = User.objects.get(id=nutritionist_id, role='nutritionist')
    except User.DoesNotExist:
        return Response({'error': 'Nutritionist not found'}, status=404)
    
    is_active = request.data.get('is_active')
    
    # Mettre à jour l'utilisateur
    nutritionist.is_active = is_active
    nutritionist.save()
    
    # Mettre à jour le profil
    try:
        profile = NutritionistProfile.objects.get(user=nutritionist)
        profile.is_available = is_active
        profile.save()
    except NutritionistProfile.DoesNotExist:
        pass
    
    status_text = 'activated' if is_active else 'deactivated'
    return Response({'message': f'Nutritionist {nutritionist.email} {status_text}'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_nutritionist(request, nutritionist_id):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        nutritionist = User.objects.get(id=nutritionist_id, role='nutritionist')
        email = nutritionist.email
        nutritionist.delete()
        return Response({'message': f'Nutritionist {email} deleted'})
    except User.DoesNotExist:
        return Response({'error': 'Nutritionist not found'}, status=404)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_admin_stats(request):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    from django.db.models import Sum, Count, Avg, F
    from datetime import datetime, timedelta
    from users.models import UserProfile, WeightHistory
    from consultations.models import Consultation
    from nutritionists.models import PatientAssignment
    from users.models import FoodLog
    
    # 1. Total Consultations (ce trimestre)
    today = datetime.now().date()
    start_of_quarter = datetime(today.year, ((today.month - 1) // 3) * 3 + 1, 1).date()
    total_consultations = Consultation.objects.filter(
        date__date__gte=start_of_quarter,
        status='completed'
    ).count()
    
    # 2. AI Track Usage (repas analysés)
    total_meals_analyzed = FoodLog.objects.count()
    
    # 3. Calcul du progrès moyen des patients
    # Progrès = (poids_initial - poids_actuel) / (poids_initial - poids_objectif) * 100
    profiles = UserProfile.objects.filter(user__role='patient')
    
    total_progress = 0
    patient_count = 0
    
    for profile in profiles:
        if profile.weight and profile.goal and profile.weight > 0:
            # Récupérer le poids initial (premier enregistrement dans WeightHistory)
            first_weight = WeightHistory.objects.filter(
                user=profile.user
            ).order_by('date').first()
            
            if first_weight:
                initial_weight = first_weight.weight_kg
                current_weight = profile.weight
                goal_weight = profile.goal
                
                # Si l'objectif est de perdre du poids
                if goal_weight < initial_weight:
                    total_to_lose = initial_weight - goal_weight
                    lost_so_far = initial_weight - current_weight
                    if total_to_lose > 0:
                        progress = min(100, max(0, (lost_so_far / total_to_lose) * 100))
                        total_progress += progress
                        patient_count += 1
                # Si l'objectif est de prendre du poids
                elif goal_weight > initial_weight:
                    total_to_gain = goal_weight - initial_weight
                    gained_so_far = current_weight - initial_weight
                    if total_to_gain > 0:
                        progress = min(100, max(0, (gained_so_far / total_to_gain) * 100))
                        total_progress += progress
                        patient_count += 1
    
    avg_user_progress = round(total_progress / patient_count) if patient_count > 0 else 0
    
    # 4. Revenue mensuel (exemple - à adapter)
    monthly_revenue = [
        {'month': 'Jan', 'revenue': 18500},
        {'month': 'Feb', 'revenue': 21200},
        {'month': 'Mar', 'revenue': 23800},
        {'month': 'Apr', 'revenue': 24600},
        {'month': 'May', 'revenue': 25800},
        {'month': 'Jun', 'revenue': 24850},
    ]
    
    # 5. Nombre de nutritionnistes actifs
    active_nutritionists = User.objects.filter(role='nutritionist', is_active=True).count()
    
    # 6. Nombre de patients actifs (avec assignation active)
    active_patients = PatientAssignment.objects.filter(is_active=True).values('patient').distinct().count()
    
    return Response({
        'total_consultations': total_consultations,
        'ai_track_usage': total_meals_analyzed,
        'avg_user_progress': avg_user_progress,
        'monthly_revenue': monthly_revenue,
        'active_nutritionists': active_nutritionists,
        'active_patients': active_patients,
    })

# admin_dashboard/views.py

from consultations.models import Consultation
from nutritionists.models import Notification
from django.utils import timezone
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trial_requests(request):
    """Admin: Récupère toutes les demandes de trial consultation"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    trials = Consultation.objects.filter(
        is_trial=True
    ).order_by('-created_at').select_related('patient', 'nutritionist')
    
    return Response([
        {
            'id': t.id,
            'patient_name': t.patient.get_full_name() or t.patient.email,
            'patient_email': t.patient.email,
            'nutritionist_name': t.nutritionist.get_full_name() if t.nutritionist else 'Unknown',
            'date': t.date.isoformat(),
            'date_display': t.date.strftime('%b %d, %Y • %I:%M %p'),
            'status': t.status,
            'notes': t.notes,
            'rejection_reason': getattr(t, 'rejection_reason', None),
            'created_at': t.created_at.isoformat(),
        }
        for t in trials
    ])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_trial_request(request, trial_id):
    """Admin: Approuve ou rejette une demande de trial"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        trial = Consultation.objects.get(id=trial_id, is_trial=True)
    except Consultation.DoesNotExist:
        return Response({'error': 'Trial request not found'}, status=404)
    
    action = request.data.get('action')
    reason = request.data.get('reason', '')
    
    if action == 'approve':
        trial.status = 'confirmed'
        trial.admin_approved_at = timezone.now()
        title = '✅ Trial Consultation Approved'
        message = f'Your free trial consultation on {trial.date.strftime("%b %d, %Y at %I:%M %p")} has been approved.'
        
        # Créer une notification pour le patient
        Notification.objects.create(
            user=trial.patient,
            notification_type='consultation_update',
            title=title,
            message=message,
            related_id=trial.id,
        )
        
        # Créer une notification pour le nutritionniste
        if trial.nutritionist:
            Notification.objects.create(
                nutritionist=trial.nutritionist,
                notification_type='consultation_reminder',
                title=title,
                message=f'Trial consultation with {trial.patient.get_full_name()} on {trial.date.strftime("%b %d, %Y at %I:%M %p")} has been approved by admin.',
                related_patient=trial.patient,
                related_id=trial.id,
                is_read=False
            )
        
    elif action == 'reject':
        trial.status = 'rejected'
        trial.rejection_reason = reason
        title = '❌ Trial Consultation Update'
        message = f'Your free trial consultation request was not approved. Reason: {reason}'
        
        # Créer une notification pour le patient
        Notification.objects.create(
            user=trial.patient,
            notification_type='consultation_update',
            title=title,
            message=message,
            related_id=trial.id,
        )
        
        # Créer une notification pour le nutritionniste
        if trial.nutritionist:
            Notification.objects.create(
                nutritionist=trial.nutritionist,
                notification_type='consultation_reminder',
                title=title,
                message=f'Trial consultation request from {trial.patient.get_full_name()} on {trial.date.strftime("%b %d, %Y at %I:%M %p")} was rejected by admin. Reason: {reason}',
                related_patient=trial.patient,
                related_id=trial.id,
                is_read=False
            )
    else:
        return Response({'error': 'Invalid action'}, status=400)
    
    trial.save()
    
    return Response({'success': True, 'message': f'Trial {action}d successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trial_stats(request):
    """Admin: Statistiques des trials"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    total = Consultation.objects.filter(is_trial=True).count()
    approved = Consultation.objects.filter(is_trial=True, status='confirmed').count()
    rejected = Consultation.objects.filter(is_trial=True, status='rejected').count()
    pending = Consultation.objects.filter(is_trial=True, status='pending').count()
    
    return Response({
        'total': total,
        'approved': approved,
        'rejected': rejected,
        'pending': pending
    })

# admin_dashboard/views.py

from nutritionists.models import PatientSubscription, SpecialOffer
from users.models import UserProfile

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_subscriptions(request):
    """Admin: Récupère tous les abonnements payés"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    subscriptions = PatientSubscription.objects.filter(
        status='active'
    ).order_by('-created_at').select_related('patient', 'special_offer')
    
    data = []
    for sub in subscriptions:
        patient = sub.patient
        profile = getattr(patient, 'user_profile', None)
        
        # Vérifier les options (has_ai, has_consultations)
        has_ai = False
        has_consultations = False
        if profile:
            has_ai = getattr(profile, 'has_ai_tracker', False)
            has_consultations = getattr(profile, 'has_consultations', False)
        
        data.append({
            'id': sub.id,
            'customer_name': patient.get_full_name() or patient.email.split('@')[0],
            'customer_email': patient.email,
            'patient_name': patient.get_full_name(),
            'patient_email': patient.email,
            'plan_name': sub.plan_name,
            'plan': sub.plan_name,
            'total_amount': float(sub.price_paid),
            'price_paid': float(sub.price_paid),
            'duration_months': sub.duration_months,
            'duration': sub.duration_months,
            'start_date': sub.start_date,
            'end_date': sub.end_date,
            'created_at': sub.created_at,
            'status': sub.status,
            'has_ai': has_ai,
            'has_consultations': has_consultations,
            'include_ai': has_ai,
            'include_consultations': has_consultations,
        })
    
    return Response(data)

from nutritionists.models import AssignmentRequest, PatientAssignment

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_requests(request):
    """Admin: Récupère toutes les demandes d'assignation en attente"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    requests = AssignmentRequest.objects.filter(
        status='pending'
    ).select_related('patient', 'nutritionist').order_by('-created_at')
    
    return Response([
        {
            'id': req.id,
            'patient_id': req.patient.id,
            'patient_name': req.patient.get_full_name() or req.patient.email,
            'patient_email': req.patient.email,
            'nutritionist_id': req.nutritionist.id,
            'nutritionist_name': req.nutritionist.get_full_name() or req.nutritionist.email,
            'nutritionist_email': req.nutritionist.email,
            'created_at': req.created_at.isoformat(),
            'created_at_display': req.created_at.strftime('%b %d, %Y at %I:%M %p'),
            'status': req.status,
        }
        for req in requests
    ])




from nutritionists.models import Notification

from nutritionists.models import Notification

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def handle_assignment_request(request, request_id):
    """Admin: Approuve ou rejette une demande d'assignation"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        assignment_req = AssignmentRequest.objects.get(id=request_id)
    except AssignmentRequest.DoesNotExist:
        return Response({'error': 'Request not found'}, status=404)
    
    action = request.data.get('action')
    reason = request.data.get('reason', '')
    
    if action == 'approve':
        # Créer l'assignation
        assignment, created = PatientAssignment.objects.get_or_create(
            patient=assignment_req.patient,
            nutritionist=assignment_req.nutritionist,
            defaults={'is_active': True}
        )
        if not created and not assignment.is_active:
            assignment.is_active = True
            assignment.save()
        
        assignment_req.status = 'approved'
        assignment_req.save()
        
        # Notification pour le patient
        Notification.objects.create(
            user=assignment_req.patient,
            notification_type='assignment_approved',
            title='✅ Assignment Request Approved!',
            message=f'Your request to be assigned to {assignment_req.nutritionist.get_full_name()} has been approved by admin.',
            related_patient=assignment_req.patient,
            related_id=assignment_req.id,
            is_read=False
        )
        
        # Notification pour le nutritionniste
        Notification.objects.create(
            nutritionist=assignment_req.nutritionist,
            notification_type='patient_assigned',
            title='🎉 New Patient Assigned!',
            message=f'{assignment_req.patient.get_full_name()} has been assigned to you by admin.',
            related_patient=assignment_req.patient,
            related_id=assignment_req.id,
            is_read=False
        )
        
        # 🔥 Notification pour l'ADMIN (sans nutritionist)
        Notification.objects.create(
            nutritionist=None,  # Pas de nutritionniste
            is_admin_notification=True,  # Marquer comme notification admin
            notification_type='admin_notification',
            title='✅ Assignment Approved',
            message=f'Patient {assignment_req.patient.get_full_name()} assigned to {assignment_req.nutritionist.get_full_name()}.',
            related_patient=assignment_req.patient,
            related_id=assignment_req.id,
            is_read=False
        )
        
    elif action == 'reject':
        assignment_req.status = 'rejected'
        assignment_req.rejection_reason = reason
        assignment_req.save()
        
        # Notification pour le patient
        Notification.objects.create(
            user=assignment_req.patient,
            notification_type='assignment_rejected',
            title='❌ Assignment Request Rejected',
            message=f'Your request to be assigned to {assignment_req.nutritionist.get_full_name()} was rejected. Reason: {reason}',
            related_patient=assignment_req.patient,
            related_id=assignment_req.id,
            is_read=False
        )
        
        # Notification pour le nutritionniste
        Notification.objects.create(
            nutritionist=assignment_req.nutritionist,
            notification_type='assignment_rejected',
            title='📋 Assignment Request Update',
            message=f'A request from {assignment_req.patient.get_full_name()} to be assigned to you was rejected by admin.',
            related_patient=assignment_req.patient,
            related_id=assignment_req.id,
            is_read=False
        )
        
        # 🔥 Notification pour l'ADMIN
        Notification.objects.create(
            nutritionist=None,
            is_admin_notification=True,
            notification_type='admin_notification',
            title='❌ Assignment Rejected',
            message=f'Request from {assignment_req.patient.get_full_name()} to {assignment_req.nutritionist.get_full_name()} was rejected.',
            related_patient=assignment_req.patient,
            related_id=assignment_req.id,
            is_read=False
        )
    
    else:
        return Response({'error': 'Invalid action'}, status=400)
    
    return Response({
        'success': True,
        'message': f'Assignment request {action}d successfully'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_stats(request):
    """Admin: Statistiques des demandes d'assignation"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    pending = AssignmentRequest.objects.filter(status='pending').count()
    approved = AssignmentRequest.objects.filter(status='approved').count()
    rejected = AssignmentRequest.objects.filter(status='rejected').count()
    total = AssignmentRequest.objects.count()
    
    return Response({
        'pending': pending,
        'approved': approved,
        'rejected': rejected,
        'total': total
    })