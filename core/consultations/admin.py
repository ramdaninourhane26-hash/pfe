from django.contrib import admin

# Register your models here.
from .models import Consultation, Message

admin.site.register(Consultation)
admin.site.register(Message)