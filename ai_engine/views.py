from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import FoodLog

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_meal_image(request):
    """Upload une image de repas"""
    if 'image' not in request.FILES:
        return Response({'error': 'No image provided'}, status=400)
    
    image = request.FILES['image']
    
    # Vérifier le type
    if not image.content_type.startswith('image/'):
        return Response({'error': 'File must be an image'}, status=400)
    
    meal_type = request.data.get('meal_type', 'lunch')
    food_name = request.data.get('food_name', 'Meal')
    calories = request.data.get('calories', 0)
    
    meal = FoodLog.objects.create(
        user=request.user,
        meal_type=meal_type,
        food_name=food_name,
        calories=int(calories),
        image=image,
    )
    
    return Response({
        'message': 'Image uploaded successfully',
        'meal_id': meal.id,
        'image_url': meal.image.url if meal.image else None
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_today_meals(request):
    from datetime import date
    from users.models import FoodLog
    
    today = date.today()
    meals = FoodLog.objects.filter(user=request.user, date=today)
    
    return Response({
        'meals': [
            {
                'id': m.id,
                'meal_type': m.meal_type,
                'food_name': m.food_name,
                'calories': m.calories,
                'image_url': m.image.url if m.image else None,
            }
            for m in meals
        ]
    })