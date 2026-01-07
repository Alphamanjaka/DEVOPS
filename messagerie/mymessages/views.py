from collections.abc import Sequence
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.http import FileResponse
from django.contrib.auth.models import User
from django.contrib import messages
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from .models import Message
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.db.models import Q  # Optional: for complex lookups
from .services import MessageImportService
from django.db.models.functions import TruncDay
from django.db.models import Count
import json


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

    return render(request, 'index.html', {
        'messages_liste': messages_liste,
        # Vérifie si l'utilisateur a la permission d'ajouter un message
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
    fields = ['contenu', 'recipient']
    template_name = 'message_form.html'
    success_url = '/messages/'
    permission_required = 'mymessages.add_message'
    raise_exception = True

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
            Q(owner=self.request.user) | Q(recipient=self.request.user)
        )

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', '-date_envoi')
        return ordering


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'message_detail.html'
    context_object_name = 'message'


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
    fields = ['contenu', 'recipient']
    template_name = 'message_form.html'
    success_url = '/messages/'
    permission_required = 'mymessages.change_message'
    raise_exception = True

    def test_func(self):
        obj = self.get_object()
        # Utilisation de getattr pour éviter les erreurs de linter (type checker)
        return getattr(obj, 'owner', None) == self.request.user or self.request.user.is_superuser
