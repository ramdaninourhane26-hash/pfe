from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_posts),
    path('create/', views.create_post),
    path('delete/<int:id>/', views.delete_post),
     path('update/<int:id>/', views.update_post),
    path('detail/<int:id>/', views.post_detail),
]
