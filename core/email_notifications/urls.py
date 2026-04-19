from django.urls import path
from .views import test_email

urlpatterns = [
    path("test/", test_email),
]