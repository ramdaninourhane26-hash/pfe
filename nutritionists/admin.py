

# nutritionists/admin.py
from django.contrib import admin
from .models import PatientAssignment, Notification

@admin.register(PatientAssignment)
class PatientAssignmentAdmin(admin.ModelAdmin):
    list_display = ('nutritionist', 'patient', 'assigned_at', 'is_active')
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        # Si c'est une nouvelle assignation (création)
        if not change:
            Notification.objects.create(
                nutritionist=obj.nutritionist,
                notification_type='patient_assigned',
                title='New Patient Assigned',
                message=f'{obj.patient.get_full_name()} has been assigned to you.',
                related_patient=obj.patient,
            )

from django.contrib import admin
from .models import SpecialOffer

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'discount_percent', 'offer_type', 'valid_until', 'is_active', 'featured']
    list_filter = ['offer_type', 'is_active', 'featured']
    search_fields = ['name']
    list_editable = ['price', 'discount_percent', 'is_active', 'featured']