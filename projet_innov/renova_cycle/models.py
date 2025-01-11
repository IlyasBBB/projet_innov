from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    CITIZEN = 'CITIZEN'
    MUNICIPALITY = 'MUNICIPALITY'
    WASTE_PICKER = 'WASTE_PICKER'
    SUPERVISOR = 'SUPERVISOR'
    
    USER_TYPES = [
        (CITIZEN, 'Citoyen'),
        (MUNICIPALITY, 'Municipalité'),
        (WASTE_PICKER, 'Chiffonier'),
        (SUPERVISOR, 'Superviseur'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES)
    phone_number = models.CharField(max_length=20)
    identity_card = models.CharField(max_length=20, blank=True, null=True)
    points = models.IntegerField(default=0)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def get_total_deposits(self):
        return self.wastedeposit_set.count()

    def get_total_points_earned(self):
        return self.wastedeposit_set.aggregate(models.Sum('points_earned'))['points_earned__sum'] or 0

    def get_total_rewards_claimed(self):
        return self.rewardclaim_set.count()

class WasteContainer(models.Model):
    ORGANIC = 'ORGANIC'
    NON_ORGANIC = 'NON_ORGANIC'
    
    WASTE_TYPES = [
        (ORGANIC, 'Organique'),
        (NON_ORGANIC, 'Non-organique'),
    ]
    
    container_id = models.CharField(max_length=50, unique=True)
    location = models.CharField(max_length=255)
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)
    capacity = models.FloatField(help_text="Capacité en kg", default=100.0)
    current_fill_level = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    last_emptied = models.DateTimeField(null=True, blank=True)
    qr_code = models.ImageField(upload_to='qr_codes/', null=True, blank=True)

    def is_full(self):
        return self.current_fill_level >= 80

    def needs_attention(self):
        return self.current_fill_level >= 50

    def update_fill_level(self, new_quantity):
        self.current_fill_level = min(100, int((new_quantity / self.capacity) * 100))
        self.save()

class WasteDeposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    container = models.ForeignKey(WasteContainer, on_delete=models.CASCADE)
    deposit_date = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField()
    qr_code_scanned = models.CharField(max_length=100)
    waste_quantity = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        if not self.points_earned:
            # Points de base selon le type de déchet
            base_points = 10 if self.container.waste_type == WasteContainer.NON_ORGANIC else 5
            self.points_earned = int(self.waste_quantity * base_points)
        
        # Mettre à jour le niveau de remplissage du conteneur
        self.container.update_fill_level(self.waste_quantity)
        
        super().save(*args, **kwargs)

class Reward(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.IntegerField()
    available_quantity = models.IntegerField()
    image = models.ImageField(upload_to='reward_images/', null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    def is_available(self):
        return self.available_quantity > 0

    def can_be_claimed_by(self, user):
        return user.points >= self.points_required and self.is_available()

class RewardClaim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    claim_date = models.DateTimeField(auto_now_add=True)
    points_spent = models.IntegerField()
    status = models.CharField(max_length=20, default='PENDING', choices=[
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('COLLECTED', 'Collecté'),
    ])

    def save(self, *args, **kwargs):
        if not self.points_spent:
            self.points_spent = self.reward.points_required
        
        if not self.pk:  # Nouvelle réclamation
            self.reward.available_quantity -= 1
            self.reward.save()
        
        super().save(*args, **kwargs)

class CollectionRecord(models.Model):
    container = models.ForeignKey(WasteContainer, on_delete=models.CASCADE)
    collector = models.ForeignKey(User, on_delete=models.CASCADE)
    collection_date = models.DateTimeField(auto_now_add=True)
    waste_quantity = models.FloatField()
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Réinitialiser le niveau de remplissage du conteneur
        self.container.current_fill_level = 0
        self.container.last_emptied = self.collection_date
        self.container.save()
        
        super().save(*args, **kwargs)
