from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .models import Notification

def get_notifications(request):
    data = Notification.objects.filter(user=request.user)
    return JsonResponse({"count": data.count()})