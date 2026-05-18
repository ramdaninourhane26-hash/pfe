from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from .models import BlogPost
from .serializers import BlogPostSerializer
from nutritionists.models import Notification

@api_view(['GET'])
@permission_classes([AllowAny])
def list_posts(request):
    """Liste tous les articles publiés (pour le site public)"""
    posts = BlogPost.objects.filter(status='published').order_by('-created_at')
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_all_posts(request):
    """Liste tous les articles (admin)"""
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    posts = BlogPost.objects.all().order_by('-created_at')
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def post_detail(request, slug):
    """Détail d'un article"""
    try:
        post = BlogPost.objects.get(slug=slug, status='published')
        serializer = BlogPostSerializer(post)
        return Response(serializer.data)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    # N'importe qui peut proposer un article, mais pas le publier directement
    data = request.data
    data['status'] = 'pending'  # Force le statut "en attente"
    data['author_user'] = request.user.id

    
    serializer = BlogPostSerializer(data=data)
    if serializer.is_valid():
        post = serializer.save()
        
        # Créer une notification pour l'admin
    
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        admin = User.objects.filter(is_superuser=True).first()
        if admin:
            Notification.objects.create(
                nutritionist=admin,
                notification_type='blog_pending',
                title='New Blog Post Pending Review',
                message=f'"{post.title}" by {post.author} needs your approval.',
                related_id=post.id,
            )
        
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_post(request, id):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    try:
        post = BlogPost.objects.get(id=id)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)
    serializer = BlogPostSerializer(post, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_post(request, id):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    try:
        post = BlogPost.objects.get(id=id)
        post.delete()
        return Response({'message': 'Post deleted'})
    except BlogPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_post(request, id):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    try:
        post = BlogPost.objects.get(id=id)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Post not found'}, status=404)
    
    action = request.data.get('action')  # 'approve' or 'reject'
    explanation = request.data.get('explanation', '')
    
    if action == 'approve':
        post.status = 'published'
        message = f'✅ Your article "{post.title}" has been approved and published!'
        title = 'Article Published'
    elif action == 'reject':
        post.status = 'rejected'
        message = f'❌ Your article "{post.title}" was not approved. Reason: {explanation}'
        title = 'Article Update'
    else:
        return Response({'error': 'Invalid action'}, status=400)
    
    post.save()
    
    
    if post.author_user:
       Notification.objects.create(
        nutritionist=post.author_user,  # ← au lieu de 'user'
        notification_type='blog_update',
        title=title,
        message=message,
        related_id=post.id,
    )
    return Response({'message': f'Article {action}ed'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pending_posts(request):
    if not request.user.is_superuser:
        return Response({'error': 'Admin access required'}, status=403)
    
    posts = BlogPost.objects.filter(status='pending').order_by('-created_at')
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)

