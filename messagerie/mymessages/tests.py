from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from .models import Message


class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='password')

    def test_message_creation(self):
        msg = Message.objects.create(contenu="Test content", owner=self.user)
        self.assertEqual(msg.contenu, "Test content")
        self.assertEqual(msg.owner, self.user)
        self.assertTrue(isinstance(msg, Message))
        self.assertEqual(str(msg), "Test content")


class AccessControlTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='basicuser', password='password')

    def test_home_accessible_authenticated(self):
        """Un utilisateur connecté accède à la home"""
        self.client.login(username='basicuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')


class MessagePermissionTest(TestCase):
    def setUp(self):
        # Utilisateur sans permission
        self.user_basic = User.objects.create_user(
            username='basic', password='password')

        # Utilisateur AVEC permission d'ajouter des messages
        self.user_poster = User.objects.create_user(
            username='poster', password='password')
        content_type = ContentType.objects.get_for_model(Message)
        permission = Permission.objects.get(
            codename='add_message', content_type=content_type)
        self.user_poster.user_permissions.add(permission)

    def test_home_context_can_post(self):
        """Vérifie que la variable 'can_post' est correctement passée au template"""
        # Cas 1: Sans permission
        self.client.login(username='basic', password='password')
        response = self.client.get(reverse('home'))
        self.assertFalse(response.context['can_post'])

        # Cas 2: Avec permission
        self.client.logout()
        self.client.login(username='poster', password='password')
        response = self.client.get(reverse('home'))
        self.assertTrue(response.context['can_post'])

    def test_add_message_view_forbidden(self):
        """Un utilisateur sans permission reçoit une 403 s'il tente de poster"""
        self.client.login(username='basic', password='password')
        response = self.client.post(reverse('add_message'), {
                                    'contenu': 'Hacker attempt'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Message.objects.count(), 0)




class MessageOwnershipTest(TestCase):
    def setUp(self):
        # Création des permissions nécessaires
        content_type = ContentType.objects.get_for_model(Message)
        perms = Permission.objects.filter(content_type=content_type, codename__in=[
                                          'change_message', 'delete_message'])

        # Propriétaire du message
        self.owner = User.objects.create_user(
            username='owner', password='password')
        self.owner.user_permissions.set(perms)

        # Autre utilisateur (avec les mêmes droits techniques, mais pas propriétaire)
        self.other = User.objects.create_user(
            username='other', password='password')
        self.other.user_permissions.set(perms)

        # Superuser
        self.admin = User.objects.create_superuser(
            username='admin', password='password', email='example@example.com')

        # Le message
        self.message = Message.objects.create(
            contenu="My precious", owner=self.owner)
        

