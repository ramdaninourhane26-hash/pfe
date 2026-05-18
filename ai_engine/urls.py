from django.urls import path
from . import views

urlpatterns = [
    path('upload-meal/', views.upload_meal_image, name='upload-meal'),
    path('today-meals/', views.get_today_meals, name='today-meals'),
]