from django.shortcuts import render, redirect
from .models import Message


def home(request):
    if request.method == "POST":
        contenu = request.POST.get("contenu")
        Message.objects.create(contenu=contenu)
        return redirect('home')

    messages_liste = Message.objects.all().order_by('-date_envoi')
    return render(request, 'index.html', {'messages_liste': messages_liste})
