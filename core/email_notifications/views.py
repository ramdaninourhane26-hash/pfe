from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .services import send_notification_email
from django.contrib.auth.models import User

def test_email(request):
    user = User.objects.first()

    send_notification_email(user, "Hello from email system 📩")

    return JsonResponse({"status": "email sent"})


