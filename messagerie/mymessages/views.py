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


@login_required
def home(request):
    # On récupère tous les messages
    messages_liste = Message.objects.all().order_by('-date_envoi')
    return render(request, 'index.html', {
        'messages_liste': messages_liste,
        # Vérifie si l'utilisateur a la permission d'ajouter un message
        'can_post': request.user.has_perm('mymessages.add_message')
    })


@login_required
@permission_required('mymessages.add_message', raise_exception=True)
@require_POST
def add_message(request):
    contenu = request.POST.get("contenu")
    if contenu:
        print("Nouveau message :", contenu)
        Message.objects.create(contenu=contenu, owner=request.user)
    return redirect('home')


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


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    fields = ['contenu']
    template_name = 'message_form.html'
    success_url = '/messages/'
    permission_required = 'mymessages.add_message'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        # Si un fichier CSV est fourni, on traite l'import
        if 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            service = MessageImportService()
            success_count, error_count = service.import_csv(csv_file)

            if success_count > 0:
                messages.success(
                    request, f"{success_count} messages importés avec succès.")
            if error_count > 0:
                messages.warning(
                    request, f"{error_count} lignes ignorées (erreurs ou en-tête).")
            return redirect('home')

        # Sinon, comportement standard de création d'un message unique
        return super().post(request, *args, **kwargs)

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
        return queryset.filter(owner=self.request.user)


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
    fields = ['contenu']
    template_name = 'message_form.html'
    success_url = '/messages/'
    permission_required = 'mymessages.change_message'
    raise_exception = True

    def test_func(self):
        obj = self.get_object()
        # Utilisation de getattr pour éviter les erreurs de linter (type checker)
        return getattr(obj, 'owner', None) == self.request.user or self.request.user.is_superuser
