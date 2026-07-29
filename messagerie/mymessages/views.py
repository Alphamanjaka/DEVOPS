import json
import io
from collections.abc import Sequence
from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.http import FileResponse
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db.models.functions import TruncDay
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .forms import MessageForm
from .models import Message
from .services import MessageImportService, get_message_stats


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
    messages_liste = Message.objects.all().order_by('-date_envoi')
    stats = get_message_stats()
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
        'chart_labels': json.dumps(stats['labels']),
        'chart_data': json.dumps(stats['data']),
        'user_labels': json.dumps(stats['user_labels']),
        'user_data': json.dumps(stats['user_data']),
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
            messages.success(request, f"{success_count} messages importés avec succès.")
        if error_count > 0:
            messages.warning(request, f"{error_count} lignes ignorées (erreurs ou en-tête).")
        return redirect('message_import')
    return render(request, 'import_messages.html')


@login_required
@require_POST
def bulk_delete_messages(request):
    message_ids = request.POST.getlist('message_ids')
    if message_ids:
        deleted_count, _ = Message.objects.filter(
            id__in=message_ids, owner=request.user).delete()
        if deleted_count > 0:
            messages.success(request, f"{deleted_count} messages supprimés.")
    return redirect('message_list')


@login_required
def export_messages_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Messages de {request.user.username}")
    p.setFont("Helvetica", 12)
    y = height - 80
    for msg in Message.objects.filter(owner=request.user).order_by('-date_envoi'):
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 12)
        date_str = msg.date_envoi.strftime("%d/%m/%Y %H:%M")
        text = f"[{date_str}] {msg.contenu}"
        p.drawString(50, y, text[:90] + ('...' if len(text) > 90 else ''))
        y -= 20
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='mes_messages.pdf')


@login_required
def export_stats_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, height - 50, "Rapport Statistique - Messagerie DevOps")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, f"Généré par : {request.user.username}")
    stats = get_message_stats()
    y = height - 110
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "1. Activité journalière (Nombre de messages)")
    y -= 25
    p.setFont("Helvetica", 12)
    for label, count in zip(stats['labels'], stats['data']):
        p.drawString(70, y, f"- {label} : {count} message(s)")
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50
    y -= 20
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "2. Répartition par utilisateur")
    y -= 25
    p.setFont("Helvetica", 12)
    for username, count in zip(stats['user_labels'], stats['user_data']):
        p.drawString(70, y, f"- {username} : {count} message(s)")
        y -= 20
    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='statistiques_dashboard.pdf')


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_form.html'
    success_url = reverse_lazy('message_list')
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
        allowed = ['date_envoi', '-date_envoi', 'owner__username', '-owner__username']
        return ordering if ordering in allowed else '-date_envoi'


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
    success_url = reverse_lazy('message_list')
    permission_required = 'mymessages.delete_message'
    raise_exception = True

    def test_func(self):
        obj = self.get_object()
        return getattr(obj, 'owner', None) == self.request.user or self.request.user.is_superuser


class MessageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'message_form.html'
    success_url = reverse_lazy('message_list')
    permission_required = 'mymessages.change_message'
    raise_exception = True

    def test_func(self):
        obj = self.get_object()
        return getattr(obj, 'owner', None) == self.request.user or self.request.user.is_superuser