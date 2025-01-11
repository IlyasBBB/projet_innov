from django.db import models
from django.contrib.auth.models import AbstractUser

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

class WasteContainer(models.Model):
    ORGANIC = 'ORGANIC'
    NON_ORGANIC = 'NON_ORGANIC'
    
    WASTE_TYPES = [
        (ORGANIC, 'Organique'),
        (NON_ORGANIC, 'Non Organique'),
    ]
    
    container_id = models.CharField(max_length=100, unique=True)
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    current_fill_level = models.IntegerField(default=0)
    last_emptied = models.DateTimeField(auto_now=True)

class WasteDeposit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    container = models.ForeignKey(WasteContainer, on_delete=models.CASCADE)
    deposit_date = models.DateTimeField(auto_now_add=True)
    points_earned = models.IntegerField()
    qr_code_scanned = models.CharField(max_length=100)

class Reward(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    points_required = models.IntegerField()
    available_quantity = models.IntegerField()

class RewardClaim(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    claim_date = models.DateTimeField(auto_now_add=True)
    points_spent = models.IntegerField()

class CollectionRecord(models.Model):
    container = models.ForeignKey(WasteContainer, on_delete=models.CASCADE)
    collector = models.ForeignKey(User, on_delete=models.CASCADE)
    collection_date = models.DateTimeField(auto_now_add=True)
    waste_quantity = models.FloatField()
