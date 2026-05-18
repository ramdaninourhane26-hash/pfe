from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.get_profile_stats, name='profile-stats'),
    path('update-weight/', views.update_weight, name='update-weight'),
    path('update-streak/', views.update_streak, name='update-streak'),
    path('weight-history/', views.get_weight_history, name='weight-history'),
    path('achievements/', views.get_achievements, name='achievements'),
    path('weekly-report/', views.get_weekly_report, name='weekly-report'),
    path('calendar/', views.get_patient_calendar, name='patient-calendar'),
    path('active-diet-plan/', views.get_active_diet_plan, name='active-diet-plan'),
    path('today-meals-checklist/', views.get_today_meals_checklist, name='today-meals-checklist'),
    path('complete-meal-checklist/<int:checklist_id>/', views.complete_meal_checklist, name='complete-meal-checklist'),
    path('complete-payment/', views.complete_payment, name='complete-payment'),
    path('my-plan/', views.get_my_plan, name='my-plan'),
    path('check-subscription/', views.check_subscription_status, name='check-subscription'),
    path('invoices/', views.get_invoices, name='invoices'),
    path('check-subscription/', views.check_subscription_status, name='check-subscription'),
    path('conversations/', views.get_conversations, name='conversations'),
    path('messages/<int:user_id>/', views.get_messages, name='messages'),
    path('send-message/', views.send_message, name='send-message'),
    path('my-nutritionist/', views.get_my_nutritionist, name='my_nutritionist'),
    path('assign-nutritionist/', views.assign_nutritionist, name='assign_nutritionist'),
    
 ]
