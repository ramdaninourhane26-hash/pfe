from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import BlogPost
from .serializers import BlogPostSerializer

@api_view(['GET'])
def list_posts(request):
    posts = BlogPost.objects.all()
    serializer = BlogPostSerializer(posts, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def create_post(request):
    serializer = BlogPostSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)


@api_view(['DELETE'])
def delete_post(request, id):
    post = BlogPost.objects.get(id=id)
    post.delete()
    return Response({"message": "deleted"})

@api_view(['PUT'])
def update_post(request, id):
    post = BlogPost.objects.get(id=id)
    serializer = BlogPostSerializer(post, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)

@api_view(['GET'])
def post_detail(request, id):
    post = BlogPost.objects.get(id=id)
    serializer = BlogPostSerializer(post)
    return Response(serializer.data)