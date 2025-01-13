from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import User, WasteContainer, WasteDeposit, Reward, RewardClaim, CollectionZone, CollectionPoint

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 
                 'user_type', 'points', 'identity_card', 'profile_picture')

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name', 'email', 
                'phone_number', 'user_type', 'points', 'identity_card', 
                'profile_picture', 'password1', 'password2'
            ),
        }),
    )
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Type d\'utilisateur', {'fields': ('user_type', 'points')}),
        ('Documents', {'fields': ('identity_card', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email')

admin.site.register(User, CustomUserAdmin)
admin.site.register(WasteContainer)
admin.site.register(WasteDeposit)
admin.site.register(Reward)
admin.site.register(RewardClaim)

@admin.register(CollectionZone)
class CollectionZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'collector', 'municipality')
    list_filter = ('collector', 'municipality')
    search_fields = ('name', 'description')

@admin.register(CollectionPoint)
class CollectionPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'zone', 'is_active')
    list_filter = ('zone', 'is_active')
    search_fields = ('name', 'address')
