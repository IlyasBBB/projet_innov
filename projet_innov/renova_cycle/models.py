from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone

class User(AbstractUser):
    CITIZEN = 'CITIZEN'
    MUNICIPALITY = 'MUNICIPALITY'
    COLLECTOR = 'COLLECTOR'
    USER_TYPES = [
        (CITIZEN, 'Citoyen'),
        (MUNICIPALITY, 'Municipalité'),
        (COLLECTOR, 'Chiffonnier'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=20)
    points = models.IntegerField(default=0)
    identity_card = models.ImageField(upload_to='identity_cards/', null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

# Modèles pour les citoyens
class WasteContainer(models.Model):
    location = models.CharField(max_length=255)
    capacity = models.IntegerField()
    current_fill_level = models.IntegerField(default=0)
    municipality = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': User.MUNICIPALITY},
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Container at {self.location} ({self.current_fill_level}/{self.capacity})"

class WasteDeposit(models.Model):
    ORGANIC = 'ORGANIC'
    NON_ORGANIC = 'NON_ORGANIC'
    WASTE_TYPES = [
        (ORGANIC, 'Organique'),
        (NON_ORGANIC, 'Non-organique'),
    ]
    
    citizen = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='deposits',
        null=True,
        blank=True
    )
    container = models.ForeignKey(
        WasteContainer, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    waste_type = models.CharField(
        max_length=20, 
        choices=WASTE_TYPES,
        null=True,
        blank=True
    )
    weight = models.FloatField(
        null=True,
        blank=True
    )
    deposit_date = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField(default=0)

    def __str__(self):
        waste_type_display = self.waste_type if self.waste_type else "Unknown"
        citizen_display = self.citizen if self.citizen else "Anonymous"
        return f"Deposit by {citizen_display} - {waste_type_display} ({self.weight}kg)"

class Reward(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.IntegerField()
    image = models.ImageField(upload_to='rewards/', null=True, blank=True)
    municipality = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': User.MUNICIPALITY},
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

class RewardClaim(models.Model):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    STATUS_CHOICES = [
        (PENDING, 'En attente'),
        (APPROVED, 'Approuvé'),
        (REJECTED, 'Rejeté'),
    ]
    
    citizen = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    claim_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default=PENDING
    )

# Modèles pour les chiffonniers
class CollectionZone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    collector = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'user_type': User.COLLECTOR},
        related_name='assigned_zones'
    )
    municipality = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'user_type': User.MUNICIPALITY},
        related_name='managed_zones'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        municipality_name = self.municipality.get_full_name() if self.municipality else "Non assigné"
        return f"{self.name} - {municipality_name}"

class CollectionPoint(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=255, default="Adresse non spécifiée")
    zone = models.ForeignKey(
        CollectionZone,
        on_delete=models.CASCADE,
        related_name='collection_points'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} - {self.zone.name}"

    class Meta:
        ordering = ['zone', 'name']

class CollectionTask(models.Model):
    PENDING = 'PENDING'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'
    
    STATUS_CHOICES = [
        (PENDING, 'En attente'),
        (IN_PROGRESS, 'En cours'),
        (COMPLETED, 'Terminé'),
        (CANCELLED, 'Annulé'),
    ]
    
    WASTE_TYPES = [
        ('PLASTIC', 'Plastique'),
        ('METAL', 'Métal'),
        ('PAPER', 'Papier'),
        ('GLASS', 'Verre'),
    ]
    
    collection_point = models.ForeignKey(
        CollectionPoint, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    collector = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': User.COLLECTOR},
        null=True,
        blank=True
    )
    waste_type = models.CharField(
        max_length=20, 
        choices=WASTE_TYPES,
        null=True,
        blank=True
    )
    estimated_weight = models.FloatField(null=True, blank=True)
    actual_weight = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default=PENDING
    )
    created_at = models.DateTimeField(default=timezone.now)
    planned_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        waste_type_display = self.get_waste_type_display() if self.waste_type else "Type non spécifié"
        point_name = self.collection_point.name if self.collection_point else "Point non spécifié"
        return f"Tâche {waste_type_display} - {point_name}"
    
    @property
    def status_color(self):
        return {
            self.PENDING: 'warning',
            self.IN_PROGRESS: 'info',
            self.COMPLETED: 'success',
            self.CANCELLED: 'danger'
        }.get(self.status, 'secondary')
    
    def save(self, *args, **kwargs):
        if self.status == self.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['planned_date', 'status']

class CollectorNotification(models.Model):
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    URGENCY_LEVELS = [
        (LOW, 'Faible'),
        (MEDIUM, 'Moyen'),
        (HIGH, 'Élevé'),
    ]

    collector = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        limit_choices_to={'user_type': User.COLLECTOR}
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    urgency = models.CharField(
        max_length=10,
        choices=URGENCY_LEVELS,
        default=MEDIUM
    )
    location = models.ForeignKey(
        'CollectionPoint',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.title} - {self.collector.get_full_name()}"

    class Meta:
        ordering = ['-created_at']

class CollectorMessage(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    is_urgent = models.BooleanField(default=False)

    def __str__(self):
        return f"Message de {self.sender.get_full_name()} à {self.recipient.get_full_name()}"

    class Meta:
        ordering = ['-sent_at']

class CollectionRecord(models.Model):
    collector = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': User.COLLECTOR}
    )
    task = models.ForeignKey(
        CollectionTask,
        on_delete=models.CASCADE
    )
    collection_date = models.DateTimeField(default=timezone.now)
    weight = models.FloatField()
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Collecte du {self.collection_date.strftime('%d/%m/%Y')} - {self.collector.get_full_name()}"
    
    class Meta:
        ordering = ['-collection_date']
