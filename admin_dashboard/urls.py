from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.get_all_users, name='all-users'),
    path('assign-patient/', views.assign_patient_to_nutritionist, name='assign-patient'),
    path('block-user/<int:user_id>/', views.block_user, name='block-user'),
    path('create-patient/', views.create_patient, name='create-patient'),
    path('nutritionists/', views.get_all_nutritionists, name='all-nutritionists'),
    path('create-nutritionist/', views.create_nutritionist, name='create-nutritionist'),
    path('nutritionist-status/<int:nutritionist_id>/', views.update_nutritionist_status, name='nutritionist-status'),
    path('delete-nutritionist/<int:nutritionist_id>/', views.delete_nutritionist, name='delete-nutritionist'),
    path('stats/', views.get_admin_stats, name='admin-stats'),
    path('trial-requests/', views.get_trial_requests, name='trial-requests'),   
    path('trial-stats/', views.get_trial_stats, name='trial-stats'),
    path('handle-trial-request/<int:request_id>/', views.handle_trial_request, name='handle-trial-request'),
    path('subscriptions/', views.get_all_subscriptions, name='subscriptions'),
     path('assignment-requests/', views.get_assignment_requests, name='assignment-requests'),
    path('assignment-requests/<int:request_id>/handle/', views.handle_assignment_request, name='handle-assignment'),
    path('assignment-stats/', views.get_assignment_stats, name='assignment-stats'),
]