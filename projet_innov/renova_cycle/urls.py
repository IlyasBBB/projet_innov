from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'renova_cycle'

urlpatterns = [
    # Routes de base
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='renova_cycle:home'), name='logout'),
    path('profile/', views.profile_view, name='profile_view'),
    
    # Routes pour les citoyens
    path('citizen/dashboard/', views.citizen_dashboard, name='citizen_dashboard'),
    path('citizen/deposit/', views.waste_deposit, name='waste_deposit'),
    path('citizen/rewards/', views.rewards_list, name='rewards_list'),
    path('citizen/claim-reward/<int:reward_id>/', views.claim_reward, name='claim_reward'),
    
    # Routes pour les municipalités
    path('municipality/dashboard/', views.municipality_dashboard, name='municipality_dashboard'),
    path('municipality/containers/', views.container_list, name='container_list'),
    path('municipality/container/add/', views.add_container, name='add_container'),
    path('municipality/container/<int:container_id>/edit/', views.edit_container, name='edit_container'),
    path('municipality/rewards/manage/', views.manage_rewards, name='manage_rewards'),
    
    # Routes pour les chiffonniers
    path('collector/dashboard/', views.collector_dashboard, name='collector_dashboard'),
    path('collector/task/update/', views.update_task_status, name='update_task_status'),
    path('collector/task/create/', views.create_task, name='create_task'),
    path('collector/notification/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('collector/message/send/', views.send_message, name='send_message'),
    path('collector/issue/report/', views.report_issue, name='report_issue'),
    path('collector/tasks/get/', views.get_tasks, name='get_tasks'),
    
    # API endpoints
    path('api/tasks/<int:task_id>/status/', views.update_task_status, name='api_update_task_status'),
    path('api/collection-points/', views.get_collection_points, name='api_get_collection_points'),
    path('api/notifications/', views.get_notifications, name='api_get_notifications'),
    path('api/messages/', views.get_messages, name='api_get_messages'),
] 