from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from .models import Message


class AccessControlTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='basicuser', password='password')

    def test_home_access_logic(self):
        """Vérifie la redirection pour utilisateur standard et l'accès pour superuser"""
        # Cas 1: Utilisateur standard -> Redirection vers la liste
        self.client.login(username='basicuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('message_list'))

        # Cas 2: Superuser -> Accès au dashboard (home)
        admin = User.objects.create_superuser(
            'admin', 'password', 'email@test.com')
        self.client.login(username='admin', password='password')
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

    def test_home_access_and_context(self):
        """Vérifie que seuls les superusers accèdent à home et ont le contexte"""
        # Cas 1: Utilisateur avec permission (mais pas superuser) -> Redirection
        self.client.login(username='poster', password='password')
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('message_list'))

        # Cas 2: Superuser -> Accès et can_post=True
        admin = User.objects.create_superuser(
            'admin_perm', 'password', 'email@test.com')
        self.client.login(username='admin_perm', password='password')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
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

    def test_owner_can_edit_delete(self):
        """Le propriétaire peut éditer et supprimer son message"""
        self.client.login(username='owner', password='password')

        # Editer
        response = self.client.post(reverse(
            'message_update', kwargs={'pk': self.message.pk}), {'contenu': 'Updated'})
        self.assertEqual(response.status_code, 302)  # Redirection après succès
        self.message.refresh_from_db()
        self.assertEqual(self.message.contenu, 'Updated')

        # Supprimer
        response = self.client.post(
            reverse('message_delete', kwargs={'pk': self.message.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(pk=self.message.pk).exists())


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

    def test_recipient_visibility(self):
        """Un utilisateur doit voir les messages qui lui sont destinés"""
        # Message envoyé par U2 à U1
        Message.objects.create(contenu="Hello U1 from U2",
                               owner=self.user2, recipient=self.user1)

        self.client.login(username='u1', password='password')
        response = self.client.get(reverse('message_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello U1 from U2")


class BulkDeleteTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1', password='password')
        self.user2 = User.objects.create_user(
            username='user2', password='password')

        self.msg1_u1 = Message.objects.create(
            contenu="Msg 1 User 1", owner=self.user1)
        self.msg2_u1 = Message.objects.create(
            contenu="Msg 2 User 1", owner=self.user1)
        self.msg1_u2 = Message.objects.create(
            contenu="Msg 1 User 2", owner=self.user2)

    def test_bulk_delete_own_messages(self):
        """User 1 supprime ses propres messages."""
        self.client.login(username='user1', password='password')

        response = self.client.post(reverse('message_bulk_delete'), {
            'message_ids': [self.msg1_u1.pk, self.msg2_u1.pk]
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Message.objects.filter(pk=self.msg1_u1.pk).exists())
        self.assertFalse(Message.objects.filter(pk=self.msg2_u1.pk).exists())
        # Le message de user 2 ne doit pas être touché
        self.assertTrue(Message.objects.filter(pk=self.msg1_u2.pk).exists())

    def test_bulk_delete_others_messages_ignored(self):
        """User 1 essaie de supprimer le message de User 2."""
        self.client.login(username='user1', password='password')

        response = self.client.post(reverse('message_bulk_delete'), {
            'message_ids': [self.msg1_u2.pk]
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Message.objects.filter(pk=self.msg1_u2.pk).exists())

    def test_bulk_delete_mixed_ownership(self):
        """User 1 supprime un mélange de ses messages et ceux des autres."""
        self.client.login(username='user1', password='password')

        response = self.client.post(reverse('message_bulk_delete'), {
            'message_ids': [self.msg1_u1.pk, self.msg1_u2.pk]
        })

        # Le sien est supprimé
        self.assertFalse(Message.objects.filter(pk=self.msg1_u1.pk).exists())
        # Celui de l'autre reste
        self.assertTrue(Message.objects.filter(pk=self.msg1_u2.pk).exists())
