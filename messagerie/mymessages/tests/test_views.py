from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from models import Message


class MessageListViewTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='u1', password='password')
        self.user2 = User.objects.create_user(
            username='u2', password='password')

        Message.objects.create(contenu="Msg U1", owner=self.user1)
        Message.objects.create(contenu="Msg U2", owner=self.user2)

    def test_list_isolation(self):
        """La vue 'message_list' ne doit montrer que les messages de l'utilisateur connecté"""
        self.client.login(username='u1', password='password')
        response = self.client.get(reverse('message_list'))

        self.assertEqual(response.status_code, 200)
        # Doit contenir le message de U1
        self.assertContains(response, "Msg U1")
        # Ne doit PAS contenir le message de U2
        self.assertNotContains(response, "Msg U2")
