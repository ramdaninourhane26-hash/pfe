"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from .import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
     path('api/accounts/', include('accounts.urls')),
    path('api/blog/', include('blog.urls')),
     path('', views.home, name='home'),
     path('about/', views.about, name='about'),
     path('feedback/', views.feedback, name='feedback'),
     path('blog/', views.blog, name='blog'),
     path('login/', views.login_view, name='login'),    
     path('register/', views.register, name='register'),
     path('user-profile/', views.user_profile, name='user_profile'),
     path('nutritionist-profile/', views.nutritionist_profile, name='nutritionist_profile'),
     path('admin-panel/', views.admin_panel, name='admin_panel'),
     path('api/users/', include('users.urls')),
     path('api/nutritionists/', include('nutritionists.urls')),
     path('api/consultations/', include('consultations.urls')),
     path('api/admin/', include('admin_dashboard.urls')),
     path('payment/', views.payment_page, name='payment'),
     path('select-nutritionist/', views.select_nutritionist, name='select_nutritionist'),
     path('trial-consultation/', views.trial_consultation, name='trial_consultation'),
] 


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)