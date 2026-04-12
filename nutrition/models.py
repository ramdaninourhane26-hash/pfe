from django.db import models

# Create your models here.

class Food(models.Model):
    name = models.CharField(max_length=100)
    calories = models.FloatField()

    def __str__(self):
        return self.name