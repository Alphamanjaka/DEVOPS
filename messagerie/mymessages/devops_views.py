import logging
import os
import shutil
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from appconf.health import db_health_check
from .models import Message

logger = logging.getLogger(__name__)

SERVICE_ICONS = {
    'Base de données': 'fa-solid fa-database',
    'Disque': 'fa-solid fa-hard-drive',
    'Uptime': 'fa-solid fa-clock',
}


def _get_uptime():
    try:
        stat = os.stat('/proc/1/cmdline')
        uptime_seconds = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds()
        hours = round(uptime_seconds / 3600, 1)
        result = f"Démarré il y a {hours}h"
        logger.debug("_get_uptime: %s", result)
        return result
    except (FileNotFoundError, OSError) as e:
        logger.warning("_get_uptime failed: %s", e)
        return "N/A"


def _get_services():
    logger.debug("_get_services called")
    disk = shutil.disk_usage("/")
    disk_usage_pct = round(disk.used / disk.total * 100, 1)
    db_healthy = db_health_check()

    services = [
        {
            'name': 'Base de données',
            'status': 'healthy' if db_healthy else 'critical',
            'info': 'Connecté' if db_healthy else 'Échec de connexion',
        },
        {
            'name': 'Disque',
            'status': 'healthy' if disk_usage_pct < 90 else 'warning' if disk_usage_pct < 95 else 'critical',
            'info': f'{disk_usage_pct}% utilisé ({round(disk.used / (1024**3), 1)} Go / {round(disk.total / (1024**3), 1)} Go)',
        },
        {
            'name': 'Uptime',
            'status': 'healthy',
            'info': _get_uptime(),
        },
    ]
    for s in services:
        s['icon'] = SERVICE_ICONS.get(s['name'], 'fa-solid fa-circle')
    logger.info("_get_services: %d services checked", len(services))
    return services


def _get_pipelines():
    pipelines = [
        {'name': 'Messagerie CI', 'status': 'success',
            'last_run': '2026-07-28 14:32', 'commit': '4f1a3b7', 'coverage': 87,
            'branch': 'main', 'author': 'CI', 'duration': '2m 14s', 'time': datetime(2026, 7, 28, 14, 32)},
        {'name': 'Frontend Build', 'status': 'running',
            'last_run': '2026-07-29 09:15', 'commit': '8d2e9c1', 'coverage': None,
            'branch': 'develop', 'author': 'CI', 'duration': '—', 'time': datetime(2026, 7, 29, 9, 15)},
        {'name': 'API Tests', 'status': 'failed',
            'last_run': '2026-07-28 22:01', 'commit': 'a3f7b2e', 'coverage': 72,
            'branch': 'feature/api', 'author': 'sarah_tech', 'duration': '1m 48s', 'time': datetime(2026, 7, 28, 22, 1)},
        {'name': 'Security Audit', 'status': 'pending',
            'last_run': None, 'commit': None, 'coverage': None,
            'branch': '—', 'author': '—', 'duration': '—', 'time': None},
        {'name': 'Docker Build', 'status': 'success',
            'last_run': '2026-07-29 06:45', 'commit': '4f1a3b7', 'coverage': None,
            'branch': 'main', 'author': 'CI', 'duration': '3m 02s', 'time': datetime(2026, 7, 29, 6, 45)},
    ]
    logger.debug("_get_pipelines: %d pipelines", len(pipelines))
    return pipelines


def _get_pipeline_stats():
    pipelines = _get_pipelines()
    stats = {
        'success': sum(1 for p in pipelines if p['status'] == 'success'),
        'fail': sum(1 for p in pipelines if p['status'] == 'failed'),
        'running': sum(1 for p in pipelines if p['status'] == 'running'),
    }
    logger.debug("_get_pipeline_stats: %s", stats)
    return stats


def _get_deployments():
    deployments = [
        {'version': 'v2.4.1', 'environment': 'Production',
            'date': datetime(2026, 7, 28, 10, 0), 'status': 'success', 'trigger': 'CI'},
        {'version': 'v2.4.0', 'environment': 'Staging',
            'date': datetime(2026, 7, 27, 16, 30), 'status': 'success', 'trigger': 'Manual'},
        {'version': 'v2.3.9', 'environment': 'Production',
            'date': datetime(2026, 7, 25, 8, 15), 'status': 'rollback', 'trigger': 'CI'},
    ]
    logger.debug("_get_deployments: %d deployments", len(deployments))
    return deployments


@login_required
def devops_dashboard(request):
    logger.info("devops_dashboard called by %s", request.user.username)
    pipelines = _get_pipelines()
    deployments = _get_deployments()
    return render(request, 'devops/dashboard.html', {
        'services': _get_services(),
        'pipelines': pipelines,
        'pipeline_stats': _get_pipeline_stats(),
        'deployments': [
            {**d, 'env': d['environment'].lower(), 'by': d['trigger'], 'time': d['date']}
            for d in deployments
        ],
    })


@login_required
def devops_deploy(request):
    logger.info("devops_deploy called by %s method=%s", request.user.username, request.method)
    if request.method == 'POST':
        environment = request.POST.get('environment', 'Staging')
        branch = request.POST.get('branch', 'main')
        version = request.POST.get('version', 'v1.0.0')
        notes = request.POST.get('notes', '')
        logger.info("devops_deploy: %s -> %s by %s", version, environment, request.user.username)
        body = (
            f"[Déploiement] {version} sur {environment}\n"
            f"Nouveau déploiement déclenché par {request.user.username}\n"
            f"Version: {version}\n"
            f"Environnement: {environment}\n"
            f"Branche: {branch}\n"
            f"Notes: {notes or 'Aucune'}"
        )
        active_users = User.objects.filter(is_active=True)
        Message.objects.bulk_create([
            Message(contenu=body, owner=request.user, recipient=user)
            for user in active_users
        ])
        logger.info("devops_deploy: notified %d users", active_users.count())
        messages.success(request, f"Déploiement {version} vers {environment} lancé. Notification envoyée à {active_users.count()} utilisateurs.")
        return redirect('devops_dashboard')
    return render(request, 'devops/deploy.html')


@login_required
def devops_notify_pipeline(request):
    pipeline_name = request.GET.get('pipeline', 'Pipeline')
    status = request.GET.get('status', 'unknown')
    logger.info("devops_notify_pipeline: %s status=%s by %s", pipeline_name, status, request.user.username)
    body = f"[Pipeline] {pipeline_name} - {status}\nPipeline {pipeline_name} terminé avec statut: {status}"
    active_users = User.objects.filter(is_active=True)
    Message.objects.bulk_create([
        Message(contenu=body, owner=request.user, recipient=user)
        for user in active_users
    ])
    logger.info("devops_notify_pipeline: notified %d users", active_users.count())
    messages.success(request, f"Notification envoyée à {active_users.count()} utilisateurs pour {pipeline_name}.")
    return redirect('devops_dashboard')
