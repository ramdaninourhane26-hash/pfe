from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  # We are not using usernames
    email = models.EmailField(unique=True)
    
    objects = UserManager()
    
    ROLE_CHOICES = (
        ('patient', 'Patient'),
        ('nutritionist', 'Nutritionist'),
        ('admin', 'Admin'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    created_at = models.DateTimeField(auto_now_add=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    specialization = models.CharField(max_length=100, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  


    def __str__(self):
       return f"{self.first_name} {self.last_name}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True) # Changed to optional
    weight = models.FloatField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    goal = models.CharField(max_length=100, null=True, blank=True)
    health_conditions = models.JSONField(default=list, blank=True)

