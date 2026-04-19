from django.db import models

# Create your models here.

class Message(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    content = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    def __str__(self):
        return self.name
class Consultation(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    date = models.DateField()
    time = models.TimeField()

    status = models.CharField(max_length=20, default="pending")

    def __str__(self):
        return f"{self.name} - {self.date}"