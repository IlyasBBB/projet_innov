# Generated by Django 5.1.4 on 2025-01-11 23:47

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('renova_cycle', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='collectionpoint',
            options={'ordering': ['zone', 'name']},
        ),
        migrations.RenameField(
            model_name='collectormessage',
            old_name='receiver',
            new_name='recipient',
        ),
        migrations.RemoveField(
            model_name='collectionpoint',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='collectionpoint',
            name='status',
        ),
        migrations.RemoveField(
            model_name='collectionpoint',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='collectionzone',
            name='center_lat',
        ),
        migrations.RemoveField(
            model_name='collectionzone',
            name='center_lng',
        ),
        migrations.RemoveField(
            model_name='collectionzone',
            name='radius',
        ),
        migrations.AddField(
            model_name='collectionpoint',
            name='address',
            field=models.CharField(default='Adresse non spécifiée', max_length=255),
        ),
        migrations.AddField(
            model_name='collectionpoint',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='collectionpoint',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='collectionzone',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='collectionzone',
            name='municipality',
            field=models.ForeignKey(blank=True, limit_choices_to={'user_type': 'MUNICIPALITY'}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='managed_zones', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='collectionzone',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='collectormessage',
            name='is_urgent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='collectornotification',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='renova_cycle.collectionpoint'),
        ),
        migrations.AddField(
            model_name='collectornotification',
            name='urgency',
            field=models.CharField(choices=[('LOW', 'Faible'), ('MEDIUM', 'Moyen'), ('HIGH', 'Élevé')], default='MEDIUM', max_length=10),
        ),
        migrations.AlterField(
            model_name='collectionpoint',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='collectionpoint',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AlterField(
            model_name='collectionzone',
            name='collector',
            field=models.ForeignKey(blank=True, limit_choices_to={'user_type': 'COLLECTOR'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_zones', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='collectionzone',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='collectornotification',
            name='collector',
            field=models.ForeignKey(limit_choices_to={'user_type': 'COLLECTOR'}, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL),
        ),
    ]
