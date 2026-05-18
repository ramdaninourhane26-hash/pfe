from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view,permission_classes, authentication_classes
from rest_framework.response import Response
from .models import User, Profile
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import status
from users.models import UserProfile 

User = get_user_model()

from django.contrib.auth import login as auth_login

@csrf_exempt
@api_view(['POST'])
def register(request):
    data = request.data
    role = data.get('role', 'patient')

    if role != 'patient':
        return Response(
            {"error": "Only patients can register. Nutritionists must be added by an administrator."},
            status=403
        )
    
    # Vérifier si l'email existe déjà
    email = data.get('email')
    if User.objects.filter(email=email).exists():
        return Response(
            {"error": "This email is already registered. Please login instead."},
            status=400
        )
    
    with transaction.atomic():
        # Create user
        user = User.objects.create_user(
            email=email,
            password=data['password'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            role=data.get('role', 'patient'),
            gender=data.get('gender'),
            phone=data.get('phone'),
            country=data.get('country'),
            specialization=None
        )

        # Create Profile
        user_profile = user.user_profile
        user_profile.weight = float(data.get('weight', 0))
        user_profile.height = float(data.get('height', 0))
        user_profile.age = int(data.get('age', 25))
        user_profile.goal = float(data.get('goal', 0))
        user_profile.health_conditions = data.get('healthConditions', [])
        user_profile.nutrition_streak = 0
        user_profile.last_streak_date = None
        user_profile.subscription_plan = 'free'
        user_profile.payment_completed = False
        user_profile.save()

        # 🔥 CONNECTER L'UTILISATEUR IMMÉDIATEMENT 🔥
        auth_login(request, user)

        return Response({
            "message": "Account created! Please complete payment to activate your plan.",
            "redirect_to": "/payment/"
        }, status=201)

        
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login

@api_view(['POST'])
@permission_classes([AllowAny]) # Allows access without CSRF/Auth
@authentication_classes([])    # Disables authentication for this specific view

def login_view(request):
    # Use .get() to avoid KeyError if data is missing
    email = request.data.get('email')
    password = request.data.get('password')

    # 1. Authenticate checks if email/password combination exists
    user = authenticate(request, email=email, password=password)

    if user is not None:
        # 2. login() sets the session cookie
        login(request._request, user)
        role = 'patient'
        if user.is_superuser:
            role = 'admin'
            redirect_to = '/admin-panel/'
        elif user.is_staff:
            role = 'nutritionist'
            redirect_to = '/nutritionist-profile/'
        else:
            role = 'patient'
            profile = user.user_profile
            needs_payment = not getattr(profile, 'payment_completed', False)
            redirect_to = "/payment/" if needs_payment else "/user-profile/"
        
        

        return Response({
           "message": "Login success",
            "role": role,
            "redirect_to": redirect_to,
            "needs_payment": needs_payment if role == 'patient' else False
        }, status=200)
    else:
        # 3. Generic error for security
        return Response(
            {"error": "Invalid email or password"}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


from django.contrib.auth import logout

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)
