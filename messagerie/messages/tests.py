from django.test import TestCase
from .models import Message


class MessageTest(TestCase):
    def test_creation_message(self):
        # On crée un message
        msg = Message.objects.create(contenu="Hello DevOps")
        # On vérifie que le message est bien enregistré
        self.assertEqual(msg.contenu, "Hello DevOps")
