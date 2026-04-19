from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.
from .models import Consultation, Message
from .serializers import ConsultationSerializer, MessageSerializer

# 📅 booking
@api_view(['GET'])
def list_consultations(request):
    consultations = Consultation.objects.all()
    serializer = ConsultationSerializer(consultations, many=True)
    return Response(serializer.data)
@api_view(['POST'])
def create_consultation(request):
    serializer = ConsultationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)


@api_view(['DELETE'])
def delete_consultation(request, id):
    try:
        c = Consultation.objects.get(id=id)
        c.delete()
        return Response({"message": "deleted"})
    except Consultation.DoesNotExist:
        return Response({"error": "not found"}, status=404)
from .serializers import ConsultationSerializer

@api_view(['PUT'])
def update_consultation(request, id):
    try:
        c = Consultation.objects.get(id=id)
    except Consultation.DoesNotExist:
        return Response({"error": "not found"}, status=404)

    serializer = ConsultationSerializer(c, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors)
# 💬 message
@api_view(['POST'])
def send_message(request):
    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors)
