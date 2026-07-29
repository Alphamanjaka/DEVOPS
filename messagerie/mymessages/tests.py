import io
import csv
from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Message
from .services import MessageImportService


class APITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='pass')
        self.other = User.objects.create_user(username='other', password='pass')
        content_type = ContentType.objects.get_for_model(Message)
        perm = Permission.objects.get(codename='add_message', content_type=content_type)
        self.user.user_permissions.add(perm)
        Message.objects.create(contenu='API Msg', owner=self.user, recipient=self.other)

    def test_api_list_requires_auth(self):
        response = self.client.get('/api/messages/')
        self.assertIn(response.status_code, [401, 403])

    def test_api_list_authenticated(self):
        self.client.login(username='apiuser', password='pass')
        response = self.client.get('/api/messages/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)

    def test_api_create_message(self):
        self.client.login(username='apiuser', password='pass')
        response = self.client.post('/api/messages/', {
            'contenu': 'Via API',
            'recipient': self.other.pk,
        }, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.filter(contenu='Via API').count(), 1)

    def test_api_schema_accessible(self):
        self.client.login(username='apiuser', password='pass')
        response = self.client.get('/api/schema/')
        self.assertEqual(response.status_code, 200)


class ReplyThreadTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='alice', password='pass')
        self.user2 = User.objects.create_user(username='bob', password='pass')
        content_type = ContentType.objects.get_for_model(Message)
        perm = Permission.objects.get(codename='add_message', content_type=content_type)
        self.user1.user_permissions.add(perm)
        self.user2.user_permissions.add(perm)
        self.parent_msg = Message.objects.create(contenu='Original', owner=self.user1, recipient=self.user2)

    def test_reply_creates_child(self):
        self.client.login(username='bob', password='pass')
        self.client.post(reverse('message_create'), {
            'contenu': 'Reply content',
            'recipient': self.user1.pk,
            'parent': self.parent_msg.pk,
        })
        self.assertEqual(self.parent_msg.replies.count(), 1)
        reply = self.parent_msg.replies.first()
        self.assertEqual(reply.contenu, 'Reply content')
        self.assertEqual(reply.owner, self.user2)

    def test_reply_shown_in_detail(self):
        Message.objects.create(contenu='Reply', owner=self.user2, recipient=self.user1, parent=self.parent_msg)
        self.client.login(username='alice', password='pass')
        response = self.client.get(reverse('message_detail', kwargs={'pk': self.parent_msg.pk}))
        self.assertContains(response, 'Reply')


class RegistrationTest(TestCase):
    def test_register_page_status(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_register_creates_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'baduser',
            'password1': 'Pass123!',
            'password2': 'DifferentPass456!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())


class ReadUnreadTest(TestCase):
    def setUp(self):
        self.sender = User.objects.create_user(username='alice', password='pass')
        self.recipient = User.objects.create_user(username='bob', password='pass')

    def test_message_unread_by_default(self):
        msg = Message.objects.create(contenu='Hello', owner=self.sender, recipient=self.recipient)
        self.assertFalse(msg.is_read)

    def test_detail_marks_as_read_for_recipient(self):
        msg = Message.objects.create(contenu='Hello', owner=self.sender, recipient=self.recipient)
        self.client.login(username='bob', password='pass')
        self.client.get(reverse('message_detail', kwargs={'pk': msg.pk}))
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)

    def test_detail_does_not_mark_as_read_for_owner(self):
        msg = Message.objects.create(contenu='Hello', owner=self.sender, recipient=self.recipient)
        self.client.login(username='alice', password='pass')
        self.client.get(reverse('message_detail', kwargs={'pk': msg.pk}))
        msg.refresh_from_db()
        self.assertFalse(msg.is_read)


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

    def test_home_access_logic(self):
        """Vérifie la redirection pour utilisateur standard et l'accès pour superuser"""
        # Cas 1: Utilisateur standard -> Redirection vers la liste
        self.client.login(username='basicuser', password='password')
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('message_list'))

        # Cas 2: Superuser -> Accès au dashboard (home)
        admin = User.objects.create_superuser(
            username='admin', password='password', email='email@test.com')
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
            username='admin_perm', password='password', email='email@test.com')
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


class ImportServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass')
        User.objects.create_user(username='bob', password='pass')

    def test_import_csv_success(self):
        csv_content = 'Hello Alice,2025-01-01,alice,\nHello Bob,2025-01-02,bob,'
        file = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'))
        service = MessageImportService()
        success, errors = service.import_csv(file)
        self.assertEqual(success, 2)
        self.assertEqual(errors, 0)
        self.assertEqual(Message.objects.count(), 2)

    def test_import_csv_unknown_user_skipped(self):
        csv_content = 'Hello,2025-01-01,ghost,'
        file = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'))
        service = MessageImportService()
        success, errors = service.import_csv(file)
        self.assertEqual(success, 0)
        self.assertEqual(errors, 1)

    def test_import_csv_with_recipient(self):
        csv_content = 'Hi Bob,2025-01-01,alice,bob'
        file = SimpleUploadedFile('test.csv', csv_content.encode('utf-8'))
        service = MessageImportService()
        success, errors = service.import_csv(file)
        self.assertEqual(success, 1)
        msg = Message.objects.first()
        self.assertEqual(msg.recipient.username, 'bob')

    def test_import_empty_file(self):
        file = SimpleUploadedFile('empty.csv', b'')
        service = MessageImportService()
        success, errors = service.import_csv(file)
        self.assertEqual(success, 0)
        self.assertEqual(errors, 0)


class ExportViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass')
        Message.objects.create(contenu='PDF test', owner=self.user)

    def test_export_messages_pdf(self):
        self.client.login(username='alice', password='pass')
        response = self.client.get(reverse('export_messages_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('mes_messages.pdf', response['Content-Disposition'])

    def test_export_stats_pdf(self):
        admin = User.objects.create_superuser(username='admin', password='pass', email='a@a.com')
        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('export_stats_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('statistiques_dashboard.pdf', response['Content-Disposition'])


class ImportViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='pass')

    def test_import_view_get(self):
        self.client.login(username='alice', password='pass')
        response = self.client.get(reverse('message_import'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'import_messages.html')

    def test_import_view_post_success(self):
        self.client.login(username='alice', password='pass')
        csv_content = 'Imported,2025-06-01,alice,'
        file = SimpleUploadedFile('data.csv', csv_content.encode('utf-8'))
        response = self.client.post(reverse('message_import'), {'csv_file': file})
        self.assertRedirects(response, reverse('message_import'))
        self.assertEqual(Message.objects.count(), 1)

    def test_import_view_post_no_file(self):
        self.client.login(username='alice', password='pass')
        response = self.client.post(reverse('message_import'), {})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)


class MessageUpdateNonOwnerTest(TestCase):
    def setUp(self):
        content_type = ContentType.objects.get_for_model(Message)
        perms = Permission.objects.filter(content_type=content_type, codename__in=['change_message'])
        self.owner = User.objects.create_user(username='owner', password='pass')
        self.owner.user_permissions.set(perms)
        self.other = User.objects.create_user(username='other', password='pass')
        self.other.user_permissions.set(perms)
        self.msg = Message.objects.create(contenu='Original', owner=self.owner)

    def test_non_owner_cannot_update(self):
        self.client.login(username='other', password='pass')
        response = self.client.post(reverse('message_update', kwargs={'pk': self.msg.pk}), {'contenu': 'Hacked'})
        self.assertEqual(response.status_code, 403)
        self.msg.refresh_from_db()
        self.assertEqual(self.msg.contenu, 'Original')


class HomePaginationTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(username='admin', password='pass', email='a@a.com')
        for i in range(20):
            Message.objects.create(contenu=f'Msg {i}', owner=self.admin)

    def test_home_pagination_context(self):
        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('home'))
        self.assertTrue(response.context['page_obj'].has_next())
        self.assertEqual(len(response.context['messages_liste']), 15)
        self.assertEqual(response.context['page_obj'].number, 1)

    def test_home_pagination_page_2(self):
        self.client.login(username='admin', password='pass')
        response = self.client.get(reverse('home') + '?page=2')
        self.assertFalse(response.context['page_obj'].has_next())
        self.assertEqual(len(response.context['messages_liste']), 5)
        self.assertEqual(response.context['page_obj'].number, 2)
