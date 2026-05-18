from django.urls import path
from . import views

urlpatterns = [
    path('nutritionists/', views.get_nutritionists, name='nutritionists'),
    path('my-consultations/', views.get_my_consultations, name='my-consultations'),
    path('book/', views.book_consultation, name='book-consultation'),
    path('cancel/<int:consultation_id>/', views.cancel_consultation, name='cancel-consultation'),
    path('nutritionist-profile/', views.get_nutritionist_profile, name='nutritionist-profile'),
    path('trial-book/', views.book_trial_consultation, name='book_trial'),
    path('trial-status/', views.get_trial_status, name='trial-status'),
    path('request-nutritionist-assignment/', views.request_nutritionist_assignment, name='request_nutritionist_assignment'),
]