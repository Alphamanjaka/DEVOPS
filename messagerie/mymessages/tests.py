from django.test import TestCase
from .models import Message


class MessageTest(TestCase):
    def test_creation_message(self):
        # On crée un message
        msg = Message.objects.create(contenu="Hello DevOps")
        # On vérifie que le message est bien enregistré
        self.assertEqual(msg.contenu, "Hello DevOps")

    def test_affichage_messages(self):
        # On crée plusieurs messages
        Message.objects.create(contenu="Message 1")
        Message.objects.create(contenu="Message 2")
        # On récupère tous les messages
        messages = Message.objects.all()
        # On vérifie qu'il y a bien 2 messages
        self.assertEqual(messages.count(), 2)

    def test_page_accueil_charge(self):
        response = self.client.get('/')
        # Vérifie que la page s'affiche sans erreur
        self.assertEqual(response.status_code, 200)
