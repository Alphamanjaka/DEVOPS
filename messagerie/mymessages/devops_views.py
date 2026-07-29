import os
import platform
import time
import shutil
import subprocess
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from appconf.health import db_health_check
from .models import Message


def _get_services():
    disk = shutil.disk_usage("/")
    disk_usage_pct = round(disk.used / disk.total * 100, 1)
    return [
        {
            'name': 'Base de données',
            'status': 'healthy' if db_health_check() else 'critical',
        },
        {
            'name': 'Disque',
            'status': 'healthy' if disk_usage_pct < 90 else 'warning' if disk_usage_pct < 95 else 'critical',
            'detail': f'{disk_usage_pct}% utilisé ({round(disk.used / (1024**3), 1)} Go / {round(disk.total / (1024**3), 1)} Go)',
        },
        {
            'name': 'Uptime',
            'status': 'healthy',
            'detail': f'Démarré il y a {round((datetime.now() - datetime.fromtimestamp(os.path.getmtime("/proc/1/cmdline"))).total_seconds() / 3600, 1)}h'
        },
    ]


def _get_pipelines():
    return [
        {'name': 'Messagerie CI', 'status': 'success',
            'last_run': '2026-07-28 14:32', 'commit': '4f1a3b7', 'coverage': 87},
        {'name': 'Frontend Build', 'status': 'running',
            'last_run': '2026-07-29 09:15', 'commit': '8d2e9c1', 'coverage': None},
        {'name': 'API Tests', 'status': 'failed',
            'last_run': '2026-07-28 22:01', 'commit': 'a3f7b2e', 'coverage': 72},
        {'name': 'Security Audit', 'status': 'pending',
            'last_run': None, 'commit': None, 'coverage': None},
        {'name': 'Docker Build', 'status': 'success',
            'last_run': '2026-07-29 06:45', 'commit': '4f1a3b7', 'coverage': None},
    ]


def _get_deployments():
    return [
        {'version': 'v2.4.1', 'environment': 'Production',
            'date': '2026-07-28 10:00', 'status': 'success', 'trigger': 'CI'},
        {'version': 'v2.4.0', 'environment': 'Staging',
            'date': '2026-07-27 16:30', 'status': 'success', 'trigger': 'Manual'},
        {'version': 'v2.3.9', 'environment': 'Production',
            'date': '2026-07-25 08:15', 'status': 'rollback', 'trigger': 'CI'},
    ]


@login_required
def devops_dashboard(request):
    return render(request, 'devops/dashboard.html', {
        'services': _get_services(),
        'pipelines': _get_pipelines(),
        'deployments': _get_deployments(),
    })


@login_required
def devops_deploy(request):
    if request.method == 'POST':
        environment = request.POST.get('environment', 'Staging')
        branch = request.POST.get('branch', 'main')
        version = request.POST.get('version', 'v1.0.0')
        notes = request.POST.get('notes', '')
        subject = f"[Déploiement] {version} sur {environment}"
        body = (
            f"Nouveau déploiement déclenché par {request.user.username}\n"
            f"Version: {version}\n"
            f"Environnement: {environment}\n"
            f"Branche: {branch}\n"
            f"Notes: {notes or 'Aucune'}"
        )
        active_users = User.objects.filter(is_active=True)
        for user in active_users:
            Message.objects.create(
                contenu=body,
                subject=subject,
                owner=request.user,
                recipient=user
            )
        messages.success(request, f"Déploiement {version} vers {environment} lancé. Notification envoyée à {active_users.count()} utilisateurs.")
        return redirect('devops_dashboard')
    return render(request, 'devops/deploy.html')


@login_required
def devops_notify_pipeline(request):
    pipeline_name = request.GET.get('pipeline', 'Pipeline')
    status = request.GET.get('status', 'unknown')
    subject = f"[Pipeline] {pipeline_name} - {status}"
    active_users = User.objects.filter(is_active=True)
    for user in active_users:
        Message.objects.create(
            contenu=f"Pipeline {pipeline_name} terminé avec statut: {status}",
            subject=subject,
            owner=request.user,
            recipient=user
        )
    messages.success(request, f"Notification envoyée à {active_users.count()} utilisateurs pour {pipeline_name}.")
    return redirect('devops_dashboard')