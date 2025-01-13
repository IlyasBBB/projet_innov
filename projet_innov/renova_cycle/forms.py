from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    User, WasteDeposit, WasteContainer, Reward,
    CollectionTask, CollectionPoint, CollectionZone
)

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    phone_number = forms.CharField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPES)
    identity_card = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'user_type', 'identity_card', 'password1', 'password2')

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')

class WasteDepositForm(forms.ModelForm):
    class Meta:
        model = WasteDeposit
        fields = ['waste_type', 'weight', 'container']
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.user_type == User.MUNICIPALITY:
            self.fields['container'].queryset = WasteContainer.objects.filter(municipality=user)

class WasteContainerForm(forms.ModelForm):
    class Meta:
        model = WasteContainer
        fields = ['location', 'capacity']

class RewardForm(forms.ModelForm):
    class Meta:
        model = Reward
        fields = ['name', 'description', 'points_required', 'image']

class CollectionTaskForm(forms.ModelForm):
    class Meta:
        model = CollectionTask
        fields = ['waste_type', 'estimated_weight', 'collection_point']
        widgets = {
            'waste_type': forms.Select(attrs={'class': 'form-control'}),
            'estimated_weight': forms.NumberInput(attrs={'class': 'form-control'}),
            'collection_point': forms.Select(attrs={'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        collector = kwargs.pop('collector', None)
        super().__init__(*args, **kwargs)
        if collector:
            zones = CollectionZone.objects.filter(collector=collector)
            self.fields['collection_point'].queryset = CollectionPoint.objects.filter(zone__in=zones) 