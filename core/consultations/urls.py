from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_consultations),
    path('create/', views.create_consultation),
    path('delete/<int:id>/', views.delete_consultation),
    path('update/<int:id>/', views.update_consultation),
    path('message/', views.send_message),
]
