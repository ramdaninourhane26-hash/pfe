from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Consultation, NutritionistProfile
from django.contrib.auth import get_user_model
from consultations.models import Consultation, ActivityLog


User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionists(request):
    """Récupère la liste des nutritionnistes disponibles"""
    nutritionists = User.objects.filter(role='nutritionist')
    
    data = []
    for n in nutritionists:
        profile = getattr(n, 'nutritionist_profile', None)
        data.append({
            'id': n.id,
            'name': n.get_full_name(),
            'email': n.email,
            'specialization': profile.specialization if profile else 'General Nutrition',
            'bio': profile.bio if profile else '',
            'experience_years': profile.experience_years if profile else 0,
            'is_available': profile.is_available if profile else True,
        })
    
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_nutritionist_profile(request):
    """Récupère le profil du nutritionniste connecté"""
    if request.user.role != 'nutritionist':
        return Response({'error': 'Unauthorized'}, status=403)
    
    profile = getattr(request.user, 'nutritionist_profile', None)
    
    return Response({
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'email': request.user.email,
        'phone': request.user.phone,
        'country': request.user.country,
        'specialization': profile.specialization if profile else '',
        'experience_years': profile.experience_years if profile else 0,
        'bio': profile.bio if profile else '',
        'is_available': profile.is_available if profile else True,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_consultations(request):
    """Récupère les consultations du patient connecté"""
    consultations = Consultation.objects.filter(patient=request.user)
    
    data = []
    for c in consultations:
        data.append({
            'id': c.id,
            'nutritionist_name': c.nutritionist.get_full_name(),
            'date': c.date.strftime('%Y-%m-%d %H:%M'),
            'status': c.status,
            'zoom_link': c.zoom_link,
            'notes': c.notes,
        })
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def book_consultation(request):
    """Réserver une consultation"""
    from datetime import datetime
    
    nutritionist_id = request.data.get('nutritionist_id')
    date_str = request.data.get('date')
    notes = request.data.get('notes', '')
    
    if not nutritionist_id or not date_str:
        return Response({'error': 'Nutritionist and date are required'}, status=400)
    
    # Vérifier que le nutritionniste existe
    try:
        nutritionist = User.objects.get(id=nutritionist_id, role='nutritionist')
    except User.DoesNotExist:
        return Response({'error': 'Nutritionist not found'}, status=404)
    
    # Vérifier que la date est valide
    try:
        date = datetime.fromisoformat(date_str)
    except:
        return Response({'error': 'Invalid date format'}, status=400)
    
    # Créer la consultation
    consultation = Consultation.objects.create(
        patient=request.user,
        nutritionist=nutritionist,
        date=date,
        status='pending',
        notes=notes,
        zoom_link=None,  # Sera généré après confirmation
    )
    
    return Response({
        'message': 'Consultation booked successfully!',
        'consultation_id': consultation.id,
        'status': consultation.status
    }, status=201)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def cancel_consultation(request, consultation_id):
    """Annuler une consultation"""
    consultation = get_object_or_404(Consultation, id=consultation_id, patient=request.user)
    
    if consultation.status == 'cancelled':
        return Response({'error': 'Consultation already cancelled'}, status=400)
    
    consultation.status = 'cancelled'
    consultation.save()
    
    return Response({'message': 'Consultation cancelled successfully'})


from nutritionists.models import Notification  


@api_view(['POST'])
def book_trial_consultation(request):
    """Réserver une consultation d'essai gratuite (une seule fois par utilisateur)"""
    data = request.data
    user = request.user
    
    # 🔥 VÉRIFIER SI L'UTILISATEUR A DÉJÀ BOOKÉ UN TRIAL 🔥
    existing_trial = Consultation.objects.filter(
        patient=user,
        is_trial=True,
        status__in=['pending', 'confirmed']  # En attente ou confirmé
    ).exists()
    
    if existing_trial:
        return Response({
            'success': False,
            'error': 'You have already booked a free trial consultation. Only one trial per user is allowed.',
            'already_booked': True
        }, status=400)
    
    from datetime import datetime
    date_str = data['slot_date']
    time_str = data['slot_time']
    consultation_date = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    
    # Créer la consultation en attente
    consultation = Consultation.objects.create(
        patient=user,
        nutritionist_id=data['nutritionist_id'],
        date=consultation_date,
        is_trial=True,
        status='pending',
        notes=f"Trial consultation requested by {user.email}"
    )
    
    # Créer une notification pour le nutritionniste
    from nutritionists.models import Notification
    Notification.objects.create(
        nutritionist_id=data['nutritionist_id'],
        notification_type='consultation_reminder',
        title='🔔 New Trial Consultation Request',
        message=f'{user.get_full_name() or user.email} has requested a FREE TRIAL consultation on {date_str} at {time_str}.',
        related_patient=user,
        related_id=consultation.id,
        is_read=False
    )
    
    return Response({
        'success': True,
        'message': 'Trial requested! The nutritionist will confirm soon.',
        'consultation_id': consultation.id
    })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_trial_status(request):
    """Vérifie si l'utilisateur a déjà booké une consultation d'essai"""
    user = request.user
    
    trial = Consultation.objects.filter(
        patient=user,
        is_trial=True
    ).order_by('-created_at').first()
    
    if trial:
        return Response({
            'has_booked_trial': True,
            'trial_info': {
                'nutritionist_name': trial.nutritionist.get_full_name() if trial.nutritionist else None,
                'date': trial.date.strftime('%B %d, %Y') if trial.date else None,
                'time': trial.date.strftime('%I:%M %p') if trial.date else None,
                'status': trial.status,
                'created_at': trial.created_at.isoformat()
            }
        })
    
    return Response({
        'has_booked_trial': False,
        'trial_info': None
    })




from nutritionists.models import AssignmentRequest,  PatientAssignment

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_nutritionist_assignment(request):
    """Patient demande un nutritionniste - envoie une requête à l'admin"""
    user = request.user
    
    if user.role != 'patient':
        return Response({'error': 'Only patients can request a nutritionist'}, status=403)
    
    nutritionist_id = request.data.get('nutritionist_id')
    
    if not nutritionist_id:
        return Response({'error': 'Nutritionist ID required'}, status=400)
    
    try:
        nutritionist = User.objects.get(id=nutritionist_id, role='nutritionist')
    except User.DoesNotExist:
        return Response({'error': 'Nutritionist not found'}, status=404)
    
    from nutritionists.models import AssignmentRequest, Notification
    
    # Supprimer les anciennes demandes en attente du même patient
    AssignmentRequest.objects.filter(patient=user, status='pending').delete()
    
    # Créer la nouvelle demande
    assignment_request = AssignmentRequest.objects.create(
        patient=user,
        nutritionist=nutritionist,
        status='pending'
    )
    
    # Notification pour l'admin
    Notification.objects.create(
        nutritionist=None,
        notification_type='assignment_request',
        title='🔔 New Assignment Request',
        message=f'{user.get_full_name() or user.email} wants to be assigned to {nutritionist.get_full_name() or nutritionist.email}.',
        related_patient=user,
        related_id=assignment_request.id,
        is_read=False
    )
    
    return Response({
        'success': True,
        'message': 'Your request has been sent to admin. You will be notified once approved.',
        'request_id': assignment_request.id
    })