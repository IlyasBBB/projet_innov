from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    User, WasteContainer, WasteDeposit, Reward, 
    RewardClaim, CollectionRecord
)
from django.core.exceptions import PermissionDenied
from django.db import models
from django.conf import settings

def home(request):
    """Vue de la page d'accueil"""
    context = {
        'total_users': User.objects.filter(user_type=User.CITIZEN).count(),
        'total_waste': CollectionRecord.objects.aggregate(Sum('waste_quantity'))['waste_quantity__sum'] or 0,
        'total_containers': WasteContainer.objects.count(),
        'total_rewards': RewardClaim.objects.count(),
        'containers': WasteContainer.objects.all()
    }
    return render(request, 'renova_cycle/home.html', context)

def register_view(request):
    """Vue d'inscription"""
    if request.method == 'POST':
        # Traitement du formulaire d'inscription
        user_type = request.POST.get('user_type')
        if user_type not in [User.CITIZEN, User.WASTE_PICKER]:
            messages.error(request, "Type d'utilisateur non autorisé.")
            return redirect('register')

        # Création de l'utilisateur
        try:
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password1'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                user_type=user_type,
                phone_number=request.POST.get('phone_number'),
                identity_card=request.POST.get('identity_card')
            )
            login(request, user)
            return redirect('home')
        except Exception as e:
            messages.error(request, str(e))
            return redirect('register')

    return render(request, 'registration/register.html')

@login_required
def citizen_dashboard(request):
    """Vue du tableau de bord pour les citoyens"""
    if request.user.user_type != User.CITIZEN:
        raise PermissionDenied
    
    context = {
        'deposits': WasteDeposit.objects.filter(user=request.user).order_by('-deposit_date'),
        'containers': WasteContainer.objects.all(),
        'available_rewards': Reward.objects.filter(available_quantity__gt=0),
        'rewards_claimed': RewardClaim.objects.filter(user=request.user).count(),
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'renova_cycle/citizen/dashboard.html', context)

@login_required
def scan_qr_code(request):
    """Vue pour scanner et valider un QR code"""
    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')
        container = get_object_or_404(WasteContainer, container_id=qr_code)
        
        # Créer un nouveau dépôt
        deposit = WasteDeposit.objects.create(
            user=request.user,
            container=container,
            qr_code_scanned=qr_code,
            waste_quantity=float(request.POST.get('quantity', 1))
        )
        
        messages.success(request, f'Dépôt enregistré ! Vous avez gagné {deposit.points_earned} points.')
        return JsonResponse({'status': 'success', 'points': deposit.points_earned})
    
    return render(request, 'renova_cycle/citizen/scan_qr.html')

@login_required
def municipality_dashboard(request):
    """Vue du tableau de bord pour la municipalité"""
    if request.user.user_type != User.MUNICIPALITY:
        raise PermissionDenied
    
    containers = WasteContainer.objects.filter(waste_type='ORGANIC')
    collections = CollectionRecord.objects.filter(
        container__waste_type='ORGANIC',
        collector=request.user
    ).order_by('-collection_date')
    
    context = {
        'containers': containers,
        'collections': collections,
        'critical_containers_count': containers.filter(current_fill_level__gte=80).count(),
        'total_collected': collections.aggregate(total=models.Sum('waste_quantity'))['total'] or 0,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
    }
    
    return render(request, 'renova_cycle/municipality/dashboard.html', context)

@login_required
def waste_picker_dashboard(request):
    """Tableau de bord pour les chiffonniers"""
    if request.user.user_type != User.WASTE_PICKER:
        raise PermissionDenied

    context = {
        'containers': WasteContainer.objects.filter(waste_type=WasteContainer.NON_ORGANIC),
        'collections': CollectionRecord.objects.filter(
            collector=request.user,
            container__waste_type=WasteContainer.NON_ORGANIC
        ).order_by('-collection_date'),
        'today_collections': CollectionRecord.objects.filter(
            collector=request.user,
            collection_date__date=timezone.now().date()
        ).aggregate(
            count=Count('id'),
            total_quantity=Sum('waste_quantity')
        )
    }
    return render(request, 'renova_cycle/waste_picker/dashboard.html', context)

@login_required
def supervisor_dashboard(request):
    """Tableau de bord pour les superviseurs"""
    if request.user.user_type != User.SUPERVISOR:
        raise PermissionDenied

    context = {
        'total_users': User.objects.count(),
        'total_waste': CollectionRecord.objects.aggregate(Sum('waste_quantity'))['waste_quantity__sum'] or 0,
        'total_points': User.objects.aggregate(Sum('points'))['points__sum'] or 0,
        'total_rewards': RewardClaim.objects.count(),
        'containers': WasteContainer.objects.all(),
        'recent_collections': CollectionRecord.objects.order_by('-collection_date')[:10],
        'recent_deposits': WasteDeposit.objects.order_by('-deposit_date')[:10],
        'critical_containers': WasteContainer.objects.filter(current_fill_level__gte=80)
    }
    return render(request, 'renova_cycle/supervisor/dashboard.html', context)

@login_required
def update_container_status(request, container_id):
    """API pour mettre à jour le statut d'un conteneur"""
    if request.method == 'POST':
        container = get_object_or_404(WasteContainer, id=container_id)
        
        # Vérifier les permissions
        if (container.waste_type == WasteContainer.ORGANIC and 
            request.user.user_type != User.MUNICIPALITY) or \
           (container.waste_type == WasteContainer.NON_ORGANIC and 
            request.user.user_type != User.WASTE_PICKER):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Créer un enregistrement de collecte
        CollectionRecord.objects.create(
            container=container,
            collector=request.user,
            waste_quantity=float(request.POST.get('quantity', 0))
        )
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def claim_reward(request, reward_id):
    """Vue pour réclamer une récompense"""
    if request.method == 'POST':
        reward = get_object_or_404(Reward, id=reward_id)
        
        if not reward.can_be_claimed_by(request.user):
            messages.error(request, "Vous n'avez pas assez de points ou la récompense n'est plus disponible.")
            return redirect('rewards_list')
        
        RewardClaim.objects.create(
            user=request.user,
            reward=reward,
            points_spent=reward.points_required
        )
        
        messages.success(request, f'Vous avez réclamé la récompense : {reward.name}')
        return redirect('rewards_list')
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    context = {
        'total_deposits': request.user.get_total_deposits(),
        'total_points_earned': request.user.get_total_points_earned(),
        'total_rewards_claimed': request.user.get_total_rewards_claimed(),
        'recent_activities': WasteDeposit.objects.filter(user=request.user).order_by('-deposit_date')[:5]
    }
    return render(request, 'renova_cycle/profile/view.html', context)

@login_required
def profile_edit(request):
    """Vue pour modifier le profil"""
    if request.method == 'POST':
        # Mise à jour des informations du profil
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.phone_number = request.POST.get('phone_number', user.phone_number)
        
        if 'profile_image' in request.FILES:
            user.profile_image = request.FILES['profile_image']
        
        user.save()
        messages.success(request, 'Profil mis à jour avec succès.')
        return redirect('profile_view')
    
    return render(request, 'renova_cycle/profile/edit.html')

@login_required
def rewards_list(request):
    """Vue pour afficher la liste des récompenses disponibles"""
    context = {
        'rewards': Reward.objects.filter(available_quantity__gt=0),
        'user_points': request.user.points,
        'user_claims': RewardClaim.objects.filter(user=request.user).order_by('-claim_date')
    }
    return render(request, 'renova_cycle/rewards/list.html', context)

@login_required
def reward_detail(request, reward_id):
    """Vue pour afficher le détail d'une récompense"""
    reward = get_object_or_404(Reward, id=reward_id)
    context = {
        'reward': reward,
        'can_claim': reward.can_be_claimed_by(request.user)
    }
    return render(request, 'renova_cycle/rewards/detail.html', context)
