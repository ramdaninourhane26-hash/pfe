from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render 
from django.contrib.auth.decorators import login_required


def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about_us.html')

def feedback(request):
    return render(request, 'feedback.html') 

def blog(request):
    return render(request, 'blog.html')

def login_view(request):
    return render(request, 'login.html')

def register(request):
    return render(request, 'register.html')

def user_profile(request):
    return render(request, 'userdash.html')

def nutritionist_profile(request):
    return render(request, 'nutritionistdash.html')

def admin_panel(request):
    return render(request, 'admindash.html')

@login_required
def payment_page(request):
    """Affiche la page de choix du plan"""
    return render(request, 'payment.html')

@login_required(login_url='/login/')
def select_nutritionist(request):
    return render(request, 'select.html')

@login_required(login_url='/login/')
def trial_consultation(request):
    return render(request, 'trial_consultation.html')