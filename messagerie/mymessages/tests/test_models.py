from django.test import TestCase
from models import Message
from django.contrib.auth.models import User



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
