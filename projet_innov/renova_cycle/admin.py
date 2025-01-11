from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, WasteContainer, WasteDeposit, Reward, RewardClaim, CollectionRecord

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'points')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Type de compte', {'fields': ('user_type', 'identity_card')}),
        ('Points', {'fields': ('points',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'user_type', 'email', 'first_name', 'last_name', 'phone_number'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(WasteContainer)
admin.site.register(WasteDeposit)
admin.site.register(Reward)
admin.site.register(RewardClaim)
admin.site.register(CollectionRecord)
