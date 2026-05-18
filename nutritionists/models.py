
# nutritionists/models.py
from django.db import models

from django.utils import timezone
from django.conf import settings

class DietPlan(models.Model):
    """Plan alimentaire créé par un nutritionniste"""

    
    nutritionist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_plans',
        limit_choices_to={'role': 'nutritionist'}
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_plans',
        limit_choices_to={'role': 'patient'}
    )
    name = models.CharField(max_length=200)  # ex: "Perte de poids - Avril 2026"
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_seasonal = models.BooleanField(default=False)  # Pour les plans saisonniers
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.patient.get_full_name()}"


class Meal(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Petit-déjeuner'),
        ('lunch', 'Déjeuner'),
        ('dinner', 'Dîner'),
        ('snack', 'Collation'),
    ]
    
    plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE, related_name='meals')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    food_name = models.CharField(max_length=200)  # ex: "Fromage blanc 0%"
    quantity = models.CharField(max_length=100)   # ex: "200g"
    calories = models.IntegerField(help_text="Calories estimées")
    order = models.IntegerField(default=0)  # Pour ordonner les repas
    
    class Meta:
        ordering = ['plan', 'meal_type', 'order']

    def __str__(self):
        return f"{self.get_meal_type_display()}: {self.food_name}"


class PatientMealChecklist(models.Model):
    STATUS_CHOICES = [
        ('pending', 'À faire'),
        ('completed', 'Fait'),
        ('skipped', 'Sauté'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='meal_checklists'
    )
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='nutritionist_meal_checklists')
    meal_name = models.CharField(max_length=200)
    meal_time = models.CharField(max_length=20, default='12:00', help_text="Heure du repas (ex: 08:00, 12:30)")
    date = models.DateField()  # La date à laquelle ce repas doit être fait
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['patient', 'meal', 'date']  # Un seul check par repas par jour
        ordering = ['date', 'meal__meal_type', 'meal__order']

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.meal_name} - {self.date}"


class PatientAssignment(models.Model):
    """Relation entre nutritionniste et patient"""
    nutritionist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_patients',
        limit_choices_to={'role': 'nutritionist'}
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_nutritionist',
        limit_choices_to={'role': 'patient'}
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['nutritionist', 'patient']
    
    def __str__(self):
        return f"{self.nutritionist.get_full_name()} -> {self.patient.get_full_name()}"
    

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('patient_assigned', 'Nouveau patient'),
        ('consultation_reminder', 'Rappel consultation'),
        ('new_message', 'Nouveau message'),
        ('plan_updated', 'Plan mis à jour'),
        ('blog_pending', 'Blog Pending'),  # ← AJOUTE
        ('blog_update', 'Blog Update'), # ← AJOUTE
        ('assignment_request', 'Demande d\'assignation'),      # ← NOUVEAU
        ('assignment_approved', 'Assignation approuvée'),     # ← NOUVEAU
        ('assignment_rejected', 'Assignation refusée'),
        ('admin_notification', 'Notification Admin'),
    ]
    

    nutritionist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        limit_choices_to={'role': 'nutritionist'},
        null=True,  
        blank=True
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='+'
    )
    related_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_notification_type_display()}: {self.title}"
    
class PatientProgress(models.Model):
    """Suivi des progrès d'un patient par le nutritionniste"""
    # Utiliser settings.AUTH_USER_MODEL au lieu de User
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='progress_records'
    )
    nutritionist = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_progress', 
        null=True, 
        blank=True
    )
    date = models.DateField(default=timezone.now)
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    body_fat = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    muscle_mass = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        patient_name = self.patient.get_full_name() or self.patient.email
        return f"{patient_name} - {self.date}"

class SpecialOffer(models.Model):

    OFFER_TYPES = [
        ('diet_plan', 'Diet Plan'),
        ('seasonal', 'Seasonal Offer'),
    ]

    # Dans SpecialOffer, ajoute ces champs si manquants
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_offers'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
   
    duration_days = models.IntegerField(default=30, help_text="Durée de l'abonnement en jours")
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    original_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    discount_percent = models.IntegerField(default=0)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES, default='diet_plan')
    
    features = models.JSONField(default=list)
    icon = models.CharField(max_length=10, default='🍽️')
    # Pour les plans alimentaires
    diet_plan = models.ForeignKey('DietPlan', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pour les offres saisonnières
    valid_until = models.DateField()
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)  # Afficher en vedette
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_offers'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ${self.price}"
    
    @property
    def is_seasonal(self):
        return self.offer_type == 'seasonal'
    
class PatientSubscription(models.Model):

    """Abonnement d'un patient à une offre"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    special_offer = models.ForeignKey(
        'SpecialOffer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions'
    )
    plan_name = models.CharField(max_length=200)
    price_paid = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Dates importantes
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Renouvellement automatique (optionnel)
    auto_renew = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.email} - {self.plan_name} ({self.status})"
    
    @property
    def is_active(self):
        """Vérifie si l'abonnement est actif et non expiré"""
        from django.utils import timezone
        return self.status == 'active' and self.end_date >= timezone.now().date()
    
    @property
    def days_left(self):
        """Nombre de jours restants"""
        from django.utils import timezone
        if self.status == 'active' and self.end_date >= timezone.now().date():
            return (self.end_date - timezone.now().date()).days
        return 0
    
    @property
    def is_expiring_soon(self):
        """Vérifie si l'abonnement expire dans moins de 7 jours"""
        return 0 < self.days_left <= 7

class PatientSubscription(models.Model):
    """Abonnement d'un patient à une offre"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    special_offer = models.ForeignKey(
        'SpecialOffer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscriptions'
    )
    plan_name = models.CharField(max_length=200)
    price_paid = models.DecimalField(max_digits=8, decimal_places=2)
    duration_months = models.IntegerField(default=1)
    
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    auto_renew = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.email} - {self.plan_name} ({self.duration_months} months)"
    
    @property
    def is_active(self):
        from django.utils import timezone
        return self.status == 'active' and self.end_date >= timezone.now().date()
    
    @property
    def days_left(self):
        from django.utils import timezone
        if self.status == 'active' and self.end_date >= timezone.now().date():
            return (self.end_date - timezone.now().date()).days
        return 0
    
    @property
    def is_expiring_soon(self):
        return 0 < self.days_left <= 7



class AssignmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('approved', 'Approuvé'),
        ('rejected', 'Refusé'),
        ('cancelled', 'Annulé'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_requests'
    )
    nutritionist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignment_requests_received'
    )
    ('cancelled', 'Annulé'),
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['patient', 'nutritionist']  # Une seule demande par couple
    
    def __str__(self):
        return f"{self.patient.email} -> {self.nutritionist.email} ({self.status})"

