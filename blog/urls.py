from django.urls import path
from . import views

urlpatterns = [
    path('posts/', views.list_posts, name='list-posts'),
    path('posts/all/', views.list_all_posts, name='all-posts'),
    path('posts/pending/', views.list_pending_posts, name='pending-posts'),  # ← Met PENDING avant slug
    path('posts/create/', views.create_post, name='create-post'),
    path('posts/update/<int:id>/', views.update_post, name='update-post'),
    path('posts/delete/<int:id>/', views.delete_post, name='delete-post'),
    path('posts/approve/<int:id>/', views.approve_post, name='approve-post'),
    path('posts/<str:slug>/', views.post_detail, name='post-detail'), 



]



