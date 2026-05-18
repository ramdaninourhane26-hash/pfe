# nutritionists/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('diet-plans/', views.create_diet_plan, name='create-diet-plan'),
    path('diet-plans/<int:plan_id>/', views.get_diet_plan, name='get-diet-plan'),
    path('stats/', views.get_nutritionist_stats, name='nutritionist-stats'),
    path('patients/', views.get_nutritionist_patients, name='nutritionist-patients'),
    path('notifications/', views.get_notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark-read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='read-all'),
    path('my-patients/', views.get_my_patients, name='my-patients'),
    path('consultation-requests/', views.get_consultation_requests, name='consultation-requests'),
    path('consultations/<int:consultation_id>/confirm/', views.confirm_consultation, name='confirm-consultation'),
    path('consultations/', views.get_nutritionist_consultations, name='nutritionist-consultations'),
    path('consultations/<int:consultation_id>/complete/', views.complete_consultation, name='complete-consultation'),
    path('calendar/', views.get_nutritionist_calendar, name='nutritionist-calendar'),
    path('patients-select/', views.get_nutritionist_patients_for_select, name='patients-select'),
    path('diet-plans/list/', views.get_nutritionist_diet_plans, name='diet-plans-list'),
    path('patients-progress/', views.get_patients_for_progress, name='patients-progress'),
    path('patient-progress/<int:patient_id>/', views.get_patient_progress, name='patient-progress'),
    path('patient-details/<int:patient_id>/', views.get_patient_details, name='patient-details'),
    path('api/patients/<int:patient_id>/progress/', views.get_patient_progress, name='patient_progress'),
    path('api/patients/<int:patient_id>/progress/add/', views.add_patient_progress, name='add_patient_progress'),
    path('special-offers/', views.get_special_offers, name='special-offers'),
    path('purchase-offer/<int:offer_id>/', views.purchase_offer, name='purchase-offer'),
    path('admin/pending-offers/', views.get_pending_offers, name='pending-offers'),
    path('admin/approve-offer/<int:offer_id>/', views.approve_offer, name='approve-offer'),
    path('admin/reject-offer/<int:offer_id>/', views.reject_offer, name='reject-offer'),
    path('public-diet-plans/', views.get_public_diet_plans, name='public-diet-plans'),
    path('create-seasonal-offer/', views.create_seasonal_offer, name='create-seasonal-offer'),
    path('consultation-requests/', views.get_consultation_requests, name='consultation-requests'),
    path('consultations/<int:consultation_id>/confirm/', views.confirm_consultation, name='confirm-consultation'),
    path('assignment-requests/', views.get_assignment_requests, name='assignment_requests'),
    path('assignment-requests/<int:request_id>/handle/', views.handle_assignment_request, name='handle_assignment_request'),
 
    
]