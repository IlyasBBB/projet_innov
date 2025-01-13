from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    User, CollectionZone, CollectionPoint, CollectionTask,
    CollectorNotification, CollectorMessage, CollectionRecord
)
from django.core.exceptions import PermissionDenied
from django.db import models
from django.conf import settings
from .forms import (
    UserRegistrationForm, UserProfileUpdateForm, WasteDepositForm,
    WasteContainerForm, RewardForm, CollectionTaskForm
)
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

def home(request):
    """Vue de la page d'accueil"""
    if not request.user.is_authenticated:
        return render(request, 'renova_cycle/home.html')
    
    user_type = request.user.user_type
    if user_type == User.CITIZEN:
        return redirect('renova_cycle:citizen_dashboard')
    elif user_type == User.MUNICIPALITY:
        return redirect('renova_cycle:municipality_dashboard')
    elif user_type == User.COLLECTOR:
        return redirect('renova_cycle:collector_dashboard')
    
    return redirect('renova_cycle:login')

def register_view(request):
    """Vue d'inscription"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie!")
            
            # Redirection basée sur le type d'utilisateur
            if user.user_type == User.CITIZEN:
                return redirect('renova_cycle:citizen_dashboard')
            elif user.user_type == User.MUNICIPALITY:
                return redirect('renova_cycle:municipality_dashboard')
            elif user.user_type == User.COLLECTOR:
                return redirect('renova_cycle:collector_dashboard')
            
        messages.error(request, "Erreur lors de l'inscription. Veuillez vérifier les informations saisies.")
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def citizen_dashboard(request):
    """Vue du tableau de bord pour les citoyens"""
    if request.user.user_type != User.CITIZEN:
        raise PermissionDenied
    
    deposits = WasteDeposit.objects.filter(citizen=request.user).order_by('-deposit_date')
    rewards = Reward.objects.all()
    
    context = {
        'deposits': deposits,
        'rewards': rewards,
        'total_points': request.user.points
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
    
    containers = WasteContainer.objects.filter(municipality=request.user)
    total_deposits = WasteDeposit.objects.filter(container__municipality=request.user).count()
    total_weight = WasteDeposit.objects.filter(
        container__municipality=request.user
    ).aggregate(total=Sum('weight'))['total'] or 0
    
    context = {
        'containers': containers,
        'total_deposits': total_deposits,
        'total_weight': total_weight,
        'containers_count': containers.count()
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
    if request.user.user_type != User.CITIZEN:
        raise PermissionDenied
    
    reward = get_object_or_404(Reward, id=reward_id)
    
    if request.user.points >= reward.points_required:
        RewardClaim.objects.create(
            citizen=request.user,
            reward=reward,
            status='PENDING'
        )
        request.user.points -= reward.points_required
        request.user.save()
        messages.success(request, f'Vous avez réclamé la récompense : {reward.name}')
    else:
        messages.error(request, 'Points insuffisants pour cette récompense')
    
    return redirect('renova_cycle:rewards_list')

@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès!')
            return redirect('renova_cycle:profile_view')
    else:
        form = UserProfileUpdateForm(instance=request.user)
    
    return render(request, 'renova_cycle/profile.html', {'form': form})

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
    if request.user.user_type != User.CITIZEN:
        raise PermissionDenied
    
    rewards = Reward.objects.all()
    return render(request, 'renova_cycle/citizen/rewards.html', {
        'rewards': rewards,
        'user_points': request.user.points
    })

@login_required
def reward_detail(request, reward_id):
    """Vue pour afficher le détail d'une récompense"""
    reward = get_object_or_404(Reward, id=reward_id)
    context = {
        'reward': reward,
        'can_claim': reward.can_be_claimed_by(request.user)
    }
    return render(request, 'renova_cycle/rewards/detail.html', context)

@login_required
def collector_dashboard(request):
    if request.user.user_type != User.COLLECTOR:
        raise PermissionDenied
    
    # Récupération des zones assignées
    assigned_zones = CollectionZone.objects.filter(collector=request.user)
    
    # Récupération explicite des points de collecte
    collection_points = CollectionPoint.objects.filter(
        zone__in=assigned_zones,
        is_active=True
    ).select_related('zone')
    
    # Statistiques
    today = timezone.now().date()
    today_collection_weight = CollectionRecord.objects.filter(
        collector=request.user,
        collection_date__date=today
    ).aggregate(total_weight=Sum('weight'))['total_weight'] or 0
    
    # Tâches actives
    active_tasks = CollectionTask.objects.filter(
        collection_point__zone__in=assigned_zones,
        status__in=['PENDING', 'IN_PROGRESS']
    ).order_by('planned_date')
    
    # Notifications avec pagination manuelle
    all_notifications = list(CollectorNotification.objects.filter(
        collector=request.user
    ).order_by('-created_at'))
    
    # Grouper les notifications par 3
    notifications_paginated = []
    for i in range(0, len(all_notifications), 3):
        group = all_notifications[i:i+3]
        notifications_paginated.append(group)

    # Messages
    all_messages = CollectorMessage.objects.filter(
        recipient=request.user
    ).order_by('-sent_at')
    recent_messages = all_messages[:5]
    unread_messages_count = all_messages.filter(read=False).count()
    
    # Historique des collectes
    collection_history = CollectionRecord.objects.filter(
        collector=request.user
    ).order_by('-collection_date')[:10]
    
    context = {
        'assigned_zones': assigned_zones,
        'collection_points': collection_points,
        'today_collection_weight': today_collection_weight,
        'active_tasks': active_tasks,
        'active_tasks_count': active_tasks.count(),
        'notifications_paginated': notifications_paginated,
        'notifications': all_notifications,  # gardé pour compatibilité
        'unread_notifications_count': len([n for n in all_notifications if not n.read]),
        'recent_messages': recent_messages,
        'unread_messages_count': unread_messages_count,
        'collection_history': collection_history
    }
    
    return render(request, 'renova_cycle/collector/dashboard.html', context)

@login_required
def update_task_status(request):
    if request.user.user_type != User.COLLECTOR:
        raise PermissionDenied
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        task_id = request.POST.get('task_id')
        new_status = request.POST.get('status')
        weight = request.POST.get('weight')
        notes = request.POST.get('notes', '')
        
        task = CollectionTask.objects.get(id=task_id)
        
        # Vérifier que le chiffonnier a accès à cette tâche
        if task.collection_point.zone.collector != request.user:
            raise PermissionDenied
        
        # Mettre à jour le statut
        task.status = new_status
        
        # Si la tâche est terminée ou annulée
        if new_status in ['COMPLETED', 'CANCELLED']:
            task.completed_at = timezone.now()
            if new_status == 'COMPLETED':
                task.actual_weight = float(weight) if weight else None
                
                # Créer un enregistrement de collecte
                CollectionRecord.objects.create(
                    collector=request.user,
                    task=task,
                    weight=float(weight) if weight else 0,
                    notes=notes,
                    collection_date=timezone.now()
                )
            
            # Créer une notification
            status_text = "terminée" if new_status == 'COMPLETED' else "annulée"
            CollectorNotification.objects.create(
                collector=request.user,
                title=f"Tâche {status_text}",
                message=f"Tâche de collecte à {task.collection_point.name} {status_text}.",
                urgency='LOW'
            )
        
        # Si la tâche est commencée
        elif new_status == 'IN_PROGRESS':
            task.started_at = timezone.now()
        
        task.save()
        
        # Rediriger vers le dashboard
        return redirect('renova_cycle:collector_dashboard')
        
    except Exception as e:
        messages.error(request, str(e))
        return redirect('renova_cycle:collector_dashboard')

@login_required
def create_task(request):
    if request.user.user_type != User.COLLECTOR:
        raise PermissionDenied
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        collection_point_id = request.POST.get('collection_point')
        waste_type = request.POST.get('waste_type')
        estimated_weight = request.POST.get('estimated_weight', '').strip()
        planned_date = request.POST.get('planned_date')

        if not all([collection_point_id, waste_type, estimated_weight, planned_date]):
            return JsonResponse({
                'status': 'error',
                'message': 'Tous les champs sont requis'
            }, status=400)

        try:
            estimated_weight = float(estimated_weight)
            if estimated_weight <= 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Le poids estimé doit être supérieur à 0'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'status': 'error',
                'message': 'Le poids estimé doit être un nombre valide'
            }, status=400)

        try:
            collection_point = CollectionPoint.objects.get(id=collection_point_id)
        except CollectionPoint.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Point de collecte invalide'
            }, status=404)

        task = CollectionTask.objects.create(
            collection_point=collection_point,
            collector=request.user,
            waste_type=waste_type,
            estimated_weight=estimated_weight,
            planned_date=planned_date,
            status='PENDING'
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Tâche créée avec succès',
            'task_id': task.id
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur lors de la création de la tâche: {str(e)}'
        }, status=500)

@login_required
def mark_notification_read(request, notification_id):
    """Vue pour marquer une notification comme lue"""
    if request.user.user_type != User.COLLECTOR:
        raise PermissionDenied
    
    notification = get_object_or_404(CollectorNotification, id=notification_id, collector=request.user)
    notification.read = True
    notification.save()
    
    return JsonResponse({'status': 'success'})

@login_required
def send_message(request):
    """Vue pour envoyer un message"""
    if request.method != 'POST':
        raise PermissionDenied
    
    receiver_id = request.POST.get('receiver_id')
    content = request.POST.get('content')
    
    try:
        receiver = User.objects.get(id=receiver_id)
        message = CollectorMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content
        )
        
        return JsonResponse({
            'status': 'success',
            'message_id': message.id
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
def get_collection_points(request):
    """API endpoint pour récupérer les points de collecte"""
    if request.user.user_type != User.COLLECTOR:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    zone = CollectionZone.objects.filter(collector=request.user).first()
    if not zone:
        return JsonResponse({'error': 'No zone assigned'}, status=404)
    
    points = CollectionPoint.objects.filter(zone=zone)
    data = []
    
    for point in points:
        data.append({
            'id': point.id,
            'name': point.name,
            'latitude': point.latitude,
            'longitude': point.longitude,
            'status': point.status,
        })
    
    return JsonResponse({'points': data})

@login_required
def get_notifications(request):
    """API endpoint pour récupérer les notifications"""
    if request.user.user_type != User.COLLECTOR:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    notifications = CollectorNotification.objects.filter(
        collector=request.user,
        read=False
    ).order_by('-created_at')[:5]
    
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'created_at': notif.created_at.isoformat(),
        })
    
    return JsonResponse({'notifications': data})

@login_required
def get_messages(request):
    """API endpoint pour récupérer les messages"""
    if request.user.user_type != User.COLLECTOR:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    messages = CollectorMessage.objects.filter(
        receiver=request.user,
        read=False
    ).order_by('-sent_at')[:5]
    
    data = []
    for msg in messages:
        data.append({
            'id': msg.id,
            'sender': {
                'id': msg.sender.id,
                'name': msg.sender.get_full_name(),
                'profile_picture': msg.sender.profile_picture.url if msg.sender.profile_picture else None,
            },
            'content': msg.content,
            'sent_at': msg.sent_at.isoformat(),
        })
    
    return JsonResponse({'messages': data})

@login_required
def waste_deposit(request):
    if request.user.user_type != User.CITIZEN:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = WasteDepositForm(request.POST)
        if form.is_valid():
            deposit = form.save(commit=False)
            deposit.citizen = request.user
            deposit.save()
            
            # Calcul des points
            points_per_kg = {
                'ORGANIC': 5,
                'NON_ORGANIC': 10
            }
            points = deposit.weight * points_per_kg.get(deposit.waste_type, 0)
            request.user.points += points
            request.user.save()
            
            messages.success(request, f'Dépôt enregistré ! Vous avez gagné {points} points.')
            return redirect('renova_cycle:citizen_dashboard')
    else:
        form = WasteDepositForm()
    
    return render(request, 'renova_cycle/citizen/waste_deposit.html', {
        'form': form,
        'containers': WasteContainer.objects.all()
    })

@login_required
def container_list(request):
    if request.user.user_type != User.MUNICIPALITY:
        raise PermissionDenied
    
    containers = WasteContainer.objects.filter(municipality=request.user)
    return render(request, 'renova_cycle/municipality/containers.html', {
        'containers': containers
    })

@login_required
def add_container(request):
    if request.user.user_type != User.MUNICIPALITY:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = WasteContainerForm(request.POST)
        if form.is_valid():
            container = form.save(commit=False)
            container.municipality = request.user
            container.save()
            messages.success(request, 'Conteneur ajouté avec succès!')
            return redirect('renova_cycle:container_list')
    else:
        form = WasteContainerForm()
    
    return render(request, 'renova_cycle/municipality/add_container.html', {
        'form': form
    })

@login_required
def edit_container(request, container_id):
    if request.user.user_type != User.MUNICIPALITY:
        raise PermissionDenied
    
    container = get_object_or_404(WasteContainer, id=container_id, municipality=request.user)
    
    if request.method == 'POST':
        form = WasteContainerForm(request.POST, instance=container)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conteneur mis à jour avec succès!')
            return redirect('renova_cycle:container_list')
    else:
        form = WasteContainerForm(instance=container)
    
    return render(request, 'renova_cycle/municipality/edit_container.html', {
        'form': form,
        'container': container
    })

@login_required
def manage_rewards(request):
    if request.user.user_type != User.MUNICIPALITY:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = RewardForm(request.POST, request.FILES)
        if form.is_valid():
            reward = form.save(commit=False)
            reward.municipality = request.user
            reward.save()
            messages.success(request, 'Récompense ajoutée avec succès!')
            return redirect('renova_cycle:manage_rewards')
    else:
        form = RewardForm()
    
    rewards = Reward.objects.filter(municipality=request.user)
    return render(request, 'renova_cycle/municipality/manage_rewards.html', {
        'form': form,
        'rewards': rewards
    })

@login_required
def report_issue(request):
    if request.user.user_type != User.COLLECTOR:
        raise PermissionDenied
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        location = CollectionPoint.objects.get(id=request.POST.get('location'))
        
        # Créer une notification pour la municipalité
        notification = CollectorNotification.objects.create(
            collector=request.user,
            title=f"Problème signalé - {request.POST.get('issue_type')}",
            message=request.POST.get('description'),
            urgency=request.POST.get('urgency'),
            location=location
        )
        
        # Si c'est urgent, envoyer aussi un message
        if request.POST.get('urgency') == 'HIGH':
            CollectorMessage.objects.create(
                sender=request.user,
                recipient=location.zone.municipality,
                content=f"URGENT: Problème signalé à {location.name}\n\n{request.POST.get('description')}",
                is_urgent=True
            )
        
        messages.success(request, 'Problème signalé avec succès!')
        return redirect('renova_cycle:collector_dashboard')
        
    except CollectionPoint.DoesNotExist:
        messages.error(request, 'Point de collecte non trouvé.')
        return redirect('renova_cycle:collector_dashboard')
    except Exception as e:
        messages.error(request, f'Une erreur est survenue : {str(e)}')
        return redirect('renova_cycle:collector_dashboard')

@login_required
def get_tasks(request):
    if request.user.user_type != User.COLLECTOR:
        raise PermissionDenied
    
    assigned_zones = CollectionZone.objects.filter(collector=request.user)
    
    active_tasks = CollectionTask.objects.filter(
        collection_point__zone__in=assigned_zones,
        status__in=['PENDING', 'IN_PROGRESS']
    ).order_by('planned_date')
    
    html = render_to_string('renova_cycle/collector/partials/tasks_list.html', {
        'active_tasks': active_tasks
    }, request=request)
    
    return JsonResponse({
        'status': 'success',
        'html': html
    })
