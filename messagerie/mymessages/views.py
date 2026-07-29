import json
import io
import os
import subprocess
import platform
import time
from datetime import timedelta
from collections.abc import Sequence
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, JsonResponse, HttpResponse, HttpResponseBadRequest
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages as django_messages
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q, Count
from django.db.models.functions import TruncDay
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .forms import MessageForm
from .models import Message
from .services import MessageImportService


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Compte créé avec succès. Bienvenue {user.username}!')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def home(request):
    if request.user.is_superuser == False:
        return redirect('message_list')
    # On récupère tous les messages
    messages_liste = Message.objects.all().order_by('-date_envoi')

    # Préparation des données pour le graphique (Messages par jour)
    daily_stats = Message.objects.annotate(date=TruncDay('date_envoi')).values(
        'date').annotate(count=Count('id')).order_by('date')

    # Conversion des données pour Chart.js
    labels = [stat['date'].strftime('%d/%m/%Y')
              for stat in daily_stats if stat['date']]
    data = [stat['count'] for stat in daily_stats if stat['date']]

    # Préparation des données pour le graphique (Messages par utilisateur)
    user_stats = Message.objects.values('owner__username').annotate(
        count=Count('id')).order_by('-count')
    user_labels = [stat['owner__username'] if stat['owner__username']
                   else 'Anonyme' for stat in user_stats]
    user_data = [stat['count'] for stat in user_stats]

    paginator = Paginator(messages_liste, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        from django.http import JsonResponse
        html = render_to_string('_message_items.html', {'messages_liste': page_obj})
        return JsonResponse({'html': html, 'has_next': page_obj.has_next(), 'page': page_obj.next_page_number() if page_obj.has_next() else None})

    return render(request, 'index.html', {
        'messages_liste': page_obj,
        'page_obj': page_obj,
        'can_post': request.user.has_perm('mymessages.add_message'),
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data),
        'user_labels': json.dumps(user_labels),
        'user_data': json.dumps(user_data),
    })


@login_required
@permission_required('mymessages.add_message', raise_exception=True)
@require_POST
def add_message(request):
    contenu = request.POST.get("contenu")
    recipient_id = request.POST.get("recipient")
    recipient = None
    if recipient_id:
        recipient = User.objects.filter(pk=recipient_id).first()

    if contenu:
        print("Nouveau message :", contenu)
        Message.objects.create(
            contenu=contenu, owner=request.user, recipient=recipient)
    return redirect('home')


@login_required
def import_messages(request):
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        service = MessageImportService()
        success_count, error_count = service.import_csv(csv_file)

        if success_count > 0:
            messages.success(
                request, f"{success_count} messages importés avec succès.")
        if error_count > 0:
            messages.warning(
                request, f"{error_count} lignes ignorées (erreurs ou en-tête).")
        return redirect('message_import')

    return render(request, 'import_messages.html')


@login_required
@require_POST
def bulk_delete_messages(request):
    message_ids = request.POST.getlist('message_ids')
    if message_ids:
        # On filtre par ID et on s'assure que l'utilisateur est bien le propriétaire
        deleted_count, _ = Message.objects.filter(
            id__in=message_ids,
            owner=request.user
        ).delete()

        if deleted_count > 0:
            messages.success(request, f"{deleted_count} messages supprimés.")

    return redirect('message_list')


@login_required
def export_messages_pdf(request):
    # Crée un buffer en mémoire pour le PDF
    buffer = io.BytesIO()
    # Crée l'objet PDF via ReportLab
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # En-tête du PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Messages de {request.user.username}")

    # Contenu
    p.setFont("Helvetica", 12)
    y = height - 80

    # Récupération des messages de l'utilisateur
    messages = Message.objects.filter(
        owner=request.user).order_by('-date_envoi')

    for message in messages:
        # Gestion du saut de page
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 12)

        date_str = message.date_envoi.strftime("%d/%m/%Y %H:%M")
        # On tronque le texte pour éviter qu'il ne sorte de la page (mise en page simple)
        text = f"[{date_str}] {message.contenu}"
        p.drawString(50, y, text[:90] + ('...' if len(text) > 90 else ''))
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='mes_messages.pdf')


@login_required
def export_stats_pdf(request):
    # Crée un buffer en mémoire pour le PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # En-tête
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 50, "Rapport Statistique - Messagerie DevOps")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, f"Généré par : {request.user.username}")

    # Récupération des données (identique à la vue home)
    daily_stats = Message.objects.annotate(date=TruncDay('date_envoi')).values(
        'date').annotate(count=Count('id')).order_by('date')
    user_stats = Message.objects.values('owner__username').annotate(
        count=Count('id')).order_by('-count')

    y = height - 110

    # Section 1: Activité par jour
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "1. Activité journalière (Nombre de messages)")
    y -= 25
    p.setFont("Helvetica", 12)

    for stat in daily_stats:
        if stat['date']:
            date_str = stat['date'].strftime('%d/%m/%Y')
            p.drawString(70, y, f"- {date_str} : {stat['count']} message(s)")
            y -= 20
            if y < 50:
                p.showPage()
                y = height - 50

    y -= 20
    # Section 2: Répartition par utilisateur
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "2. Répartition par utilisateur")
    y -= 25
    p.setFont("Helvetica", 12)

    for stat in user_stats:
        username = stat['owner__username'] if stat['owner__username'] else 'Anonyme'
        p.drawString(70, y, f"- {username} : {stat['count']} message(s)")
        y -= 20

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='statistiques_dashboard.pdf')


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_form.html'
    success_url = '/messages/'
    permission_required = 'mymessages.add_message'
    raise_exception = True

    def get_initial(self):
        initial = super().get_initial()
        parent_pk = self.request.GET.get('parent')
        if parent_pk:
            parent = get_object_or_404(Message, pk=parent_pk)
            initial['parent'] = parent.pk
            initial['recipient'] = parent.owner
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        parent_pk = self.request.GET.get('parent')
        if parent_pk:
            parent = get_object_or_404(Message, pk=parent_pk)
            context['parent_message'] = parent
        return context

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = 'message_list.html'
    context_object_name = 'messages'
    ordering = ['-date_envoi']
    paginate_by = 10

    def get_queryset(self) -> QuerySet[Any]:
        queryset = super().get_queryset()
        search_query = self.request.GET.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(contenu__icontains=search_query)
                | Q(owner__username__icontains=search_query)
            ).distinct()
        return queryset.filter(
            Q(owner=self.request.user) | Q(recipient=self.request.user) | Q(recipients=self.request.user)
        ).distinct()

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', '-date_envoi')
        return ordering


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'message_detail.html'
    context_object_name = 'message'

    def get_object(self, *args, **kwargs):
        obj = super().get_object(*args, **kwargs)
        user = self.request.user
        is_recipient = obj.recipient == user or obj.recipients.filter(pk=user.pk).exists()
        if is_recipient and not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=['is_read'])
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['replies'] = self.object.replies.all().select_related('owner', 'recipient').order_by('date_envoi')
        return context


class MessageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Message
    template_name = 'message_confirm_delete.html'
    success_url = '/messages/'
    permission_required = 'mymessages.delete_message'
    raise_exception = True

    def test_func(self):
        obj = self.get_object()
        # Utilisation de getattr pour éviter les erreurs de linter (type checker)
        return getattr(obj, 'owner', None) == self.request.user or self.request.user.is_superuser


class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_form.html'
    success_url = '/messages/'
    permission_required = 'mymessages.change_message'
    raise_exception = True

    def test_func(self):
        obj = self.get_object()
        return getattr(obj, 'owner', None) == self.request.user or self.request.user.is_superuser


# ---------------------------------------------------------------------------
# DEVOPS FEATURES
# ---------------------------------------------------------------------------

RUNNING_IN_DOCKER = os.path.exists('/.dockerenv')


def _check_db():
    try:
        with connection.cursor() as c:
            c.execute('SELECT 1')
        return True, None
    except Exception as e:
        return False, str(e)


def _check_disk():
    try:
        if platform.system() == 'Windows':
            usage = os.popen('wmic logicaldisk get size,freespace,caption 2>nul').read()
            return True, usage[:200]
        stat = os.statvfs('/')
        free = stat.f_bavail * stat.f_frsize
        total = stat.f_blocks * stat.f_frsize
        pct = int((free / total) * 100)
        return True, f"{pct}% libre ({free // (1024**3)} Go / {total // (1024**3)} Go)"
    except Exception as e:
        return False, str(e)


def _check_uptime():
    try:
        if RUNNING_IN_DOCKER:
            out = os.popen('cat /proc/uptime 2>/dev/null').read().strip()
            if out:
                secs = float(out.split()[0])
                days = int(secs // 86400)
                hours = int((secs % 86400) // 3600)
                return f"{days}j {hours}h"
        return "N/A"
    except Exception:
        return "N/A"


def _get_pipelines():
    return [
        {'name': 'Build & Test',  'status': 'success', 'branch': 'main',   'commit': 'a3f2b1e', 'author': 'root',      'duration': '2m 14s', 'time': timezone.now() - timedelta(minutes=15)},
        {'name': 'Analyse Sonar', 'status': 'success', 'branch': 'main',   'commit': 'a3f2b1e', 'author': 'alice_admin', 'duration': '4m 07s', 'time': timezone.now() - timedelta(minutes=12)},
        {'name': 'Build & Test',  'status': 'fail',    'branch': 'feature/api', 'commit': 'b7e9c3d', 'author': 'john_user',  'duration': '1m 52s', 'time': timezone.now() - timedelta(minutes=5)},
        {'name': 'Docker Build',  'status': 'running', 'branch': 'main',   'commit': 'a3f2b1e', 'author': 'root',      'duration': '…',       'time': timezone.now() - timedelta(minutes=2)},
        {'name': 'Deploy Staging', 'status': 'success', 'branch': 'main',   'commit': 'a3f2b1e', 'author': 'alice_admin', 'duration': '1m 08s', 'time': timezone.now() - timedelta(hours=1)},
        {'name': 'Deploy Production', 'status': 'success', 'branch': 'main', 'commit': 'd4f5a6b', 'author': 'root', 'duration': '2m 31s', 'time': timezone.now() - timedelta(hours=3)},
    ]


def _get_deployments():
    return [
        {'version': 'v2.4.1', 'env': 'production',  'status': 'success', 'by': 'root',       'time': timezone.now() - timedelta(hours=3)},
        {'version': 'v2.4.0', 'env': 'production',  'status': 'success', 'by': 'alice_admin', 'time': timezone.now() - timedelta(days=1)},
        {'version': 'v2.4.0', 'env': 'staging',     'status': 'success', 'by': 'alice_admin', 'time': timezone.now() - timedelta(days=1, hours=2)},
        {'version': 'v2.3.1', 'env': 'production',  'status': 'fail',    'by': 'root',       'time': timezone.now() - timedelta(days=3)},
        {'version': 'v2.3.0', 'env': 'production',  'status': 'success', 'by': 'john_user',  'time': timezone.now() - timedelta(days=5)},
    ]


@login_required
def devops_dashboard(request):
    db_ok, db_err = _check_db()
    disk_ok, disk_info = _check_disk()

    services = [
        {'name': 'Base de données',  'icon': 'fa-database', 'status': 'up' if db_ok else 'down', 'info': None if db_ok else db_err},
        {'name': 'Disque',           'icon': 'fa-hard-drive', 'status': 'up' if disk_ok else 'down', 'info': disk_info if disk_ok else disk_err},
        {'name': 'Application',      'icon': 'fa-server',    'status': 'up', 'info': f'Uptime: {_check_uptime()}'},
        {'name': 'Cache (Redis)',    'icon': 'fa-bolt',      'status': 'warn', 'info': 'Non configuré'},
    ]

    context = {
        'pipelines': _get_pipelines(),
        'services': services,
        'deployments': _get_deployments(),
        'pipeline_stats': {
            'success': sum(1 for p in _get_pipelines() if p['status'] == 'success'),
            'fail': sum(1 for p in _get_pipelines() if p['status'] == 'fail'),
            'running': sum(1 for p in _get_pipelines() if p['status'] == 'running'),
        },
    }
    return render(request, 'devops/dashboard.html', context)


@login_required
@require_POST
def devops_notify_pipeline(request):
    status = request.POST.get('status', '')
    pipeline = request.POST.get('pipeline', '')
    users = User.objects.filter(is_active=True)
    msg = Message.objects.create(
        contenu=f"[CI/CD] Pipeline « {pipeline} » terminé avec le statut : {status.upper()}",
        owner=request.user,
        is_read=False,
    )
    msg.recipients.set(users)
    msg.save()
    django_messages.success(request, "Notification envoyée à toute l'équipe.")
    return redirect('devops_dashboard')


@login_required
def devops_deploy(request):
    if request.method == 'POST':
        env = request.POST.get('environment', 'staging')
        branch = request.POST.get('branch', 'main')
        version = request.POST.get('version', '').strip() or f"v{timezone.now().strftime('%Y%m%d.%H%M')}"
        users = User.objects.filter(is_active=True)
        msg = Message.objects.create(
            contenu=(
                f"[DÉPLOIEMENT] {version} déployé sur **{env}** "
                f"(branche: {branch}) par {request.user.username}\n"
                f"Statut : en cours…"
            ),
            owner=request.user,
            is_read=False,
        )
        msg.recipients.set(users)
        msg.save()
        django_messages.success(request, f"Déploiement {version} lancé sur {env}. Équipe notifiée.")
        return redirect('devops_deploy')
    return render(request, 'devops/deploy.html')


@csrf_exempt
def github_webhook(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("POST only")
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    event = request.META.get('HTTP_X_GITHUB_EVENT', 'push')
    owner = User.objects.filter(is_superuser=True).first()
    if not owner:
        return JsonResponse({'error': 'No admin user'}, status=500)

    if event == 'push':
        ref = payload.get('ref', '')
        branch = ref.replace('refs/heads/', '') if ref else 'unknown'
        commits = payload.get('commits', [])
        count = len(commits)
        sender = payload.get('sender', {}).get('login', 'unknown')
        repo = payload.get('repository', {}).get('full_name', 'unknown')
        msg_text = (
            f"[GITHUB] Push sur {repo}/{branch} par {sender}\n"
            f"{count} commit(s) - Voir les détails sur GitHub"
        )
        if commits:
            msg_text += "\n" + "\n".join(
                f"  - {c.get('message', '').split(chr(10))[0][:60]} ({c.get('id', '')[:7]})"
                for c in commits[:5]
            )
    elif event == 'pull_request':
        pr = payload.get('pull_request', {})
        action = payload.get('action', 'opened')
        title = pr.get('title', '')
        url = pr.get('html_url', '')
        sender = payload.get('sender', {}).get('login', 'unknown')
        repo = payload.get('repository', {}).get('full_name', 'unknown')
        msg_text = f"[GITHUB] PR {action} sur {repo} par {sender}\n{title}\n{url}"
    else:
        msg_text = f"[GITHUB] Événement {event} reçu depuis {payload.get('repository', {}).get('full_name', 'unknown')}"

    users = User.objects.filter(is_active=True)
    msg = Message.objects.create(contenu=msg_text, owner=owner, is_read=False)
    msg.recipients.set(users)
    msg.save()
    return JsonResponse({'ok': True, 'message_id': msg.pk})
