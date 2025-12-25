from typing import Any
from django.db.models.query import QuerySet
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST
from .models import Message
from django.views.generic import ListView, DetailView, DeleteView, UpdateView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.db.models import Q  # Optional: for complex lookups


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


class MessageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Message
    fields = ['contenu']
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
