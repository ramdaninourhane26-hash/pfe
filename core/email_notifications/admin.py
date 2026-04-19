from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import EmailLog

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'subject', 'created_at')
    list_filter = ('created_at', 'email')
    search_fields = ('email', 'subject', 'message')
    ordering = ('-created_at',)