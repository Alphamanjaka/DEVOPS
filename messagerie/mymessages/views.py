from django.shortcuts import render, redirect
from .models import Message


def home(request):
    if request.method == "POST":
        print("Contenu du message reçu:", request.POST.get("contenu"))
        contenu = request.POST.get("contenu")
        Message.objects.create(contenu=contenu)
        return redirect('home')
    # On récupère tous les messages
    print("Récupération des messages depuis la base de données")
    messages_liste = Message.objects.all().order_by('-date_envoi')
    return render(request, 'index.html', {'messages_liste': messages_liste})
