from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'renova_cycle'

urlpatterns = [
    # Pages principales
    path('', views.home, name='home'),
    
    # Authentification
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Tableaux de bord
    path('citizen/dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('municipality/dashboard/', views.municipality_dashboard, name='municipality_dashboard'),
    path('waste-picker/dashboard/', views.waste_picker_dashboard, name='waste_picker_dashboard'),
    path('supervisor/dashboard/', views.supervisor_dashboard, name='supervisor_dashboard'),
    
    # Gestion des déchets
    path('scan-qr/', views.scan_qr_code, name='scan_qr'),
    path('container/<int:container_id>/update/', views.update_container_status, name='update_container'),
    
    # Récompenses
    path('rewards/', views.rewards_list, name='rewards_list'),
    path('rewards/<int:reward_id>/', views.reward_detail, name='reward_detail'),
    path('rewards/<int:reward_id>/claim/', views.claim_reward, name='claim_reward'),
    
    # Profil utilisateur
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
] 