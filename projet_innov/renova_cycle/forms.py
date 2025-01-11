from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, WasteDeposit, RewardClaim, CollectionRecord

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'user_type', 'identity_card')

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        identity_card = cleaned_data.get('identity_card')

        if user_type == User.WASTE_PICKER and not identity_card:
            raise forms.ValidationError(
                "Le numéro CIN est obligatoire pour les chiffonniers."
            )
        return cleaned_data

class UserProfileUpdateForm(forms.ModelForm):
    current_password = forms.CharField(widget=forms.PasswordInput, required=False)
    new_password = forms.CharField(widget=forms.PasswordInput, required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_image')

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and new_password != confirm_password:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

class WasteDepositForm(forms.ModelForm):
    class Meta:
        model = WasteDeposit
        fields = ('container', 'qr_code_scanned')
        widgets = {
            'qr_code_scanned': forms.HiddenInput()
        }

    def clean_qr_code_scanned(self):
        qr_code = self.cleaned_data['qr_code_scanned']
        container = self.cleaned_data.get('container')
        
        if container and container.container_id != qr_code:
            raise forms.ValidationError("Code QR invalide pour ce conteneur.")
        return qr_code

class RewardClaimForm(forms.ModelForm):
    class Meta:
        model = RewardClaim
        fields = ('reward',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        reward = cleaned_data.get('reward')

        if reward:
            if self.user.points < reward.points_required:
                raise forms.ValidationError(
                    f"Vous n'avez pas assez de points. Il vous manque {reward.points_required - self.user.points} points."
                )
            if reward.available_quantity < 1:
                raise forms.ValidationError("Cette récompense n'est plus disponible.")
        return cleaned_data

class CollectionRecordForm(forms.ModelForm):
    class Meta:
        model = CollectionRecord
        fields = ('container', 'waste_quantity')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        container = cleaned_data.get('container')

        if container:
            if (container.waste_type == 'ORGANIC' and 
                self.user.user_type != User.MUNICIPALITY) or \
               (container.waste_type == 'NON_ORGANIC' and 
                self.user.user_type != User.WASTE_PICKER):
                raise forms.ValidationError(
                    "Vous n'êtes pas autorisé à collecter ce type de déchets."
                )
        return cleaned_data

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

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.user_type = self.cleaned_data['user_type']
        
        if commit:
            user.save()
        return user 