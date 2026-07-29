"""
Seed script: reset database and load important demo data.
Run: docker exec -it devops-web-1 python seed_data.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messagerie.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from mymessages.models import Message


def clean():
    Message.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()
    print("  Cleaned existing data")


def create_users():
    root, _ = User.objects.get_or_create(username='root', defaults={'is_superuser': True})
    root.set_password('root123')
    root.is_staff = True
    root.save()

    users_data = [
        ('john_user', 'john@example.com', False),
        ('alice_admin', 'alice@example.com', True),
        ('bob_user', 'bob@example.com', False),
        ('sarah_tech', 'sarah@example.com', False),
    ]
    users = {'root': root}
    for username, email, is_staff in users_data:
        u, _ = User.objects.get_or_create(username=username)
        u.set_password('pass1234')
        u.email = email
        u.is_staff = is_staff
        u.save()
        users[username] = u
    print(f"  Created {len(users)} users")
    return users


def create_messages(users):
    now = timezone.now()
    content_data = [
        ("Bienvenue sur la nouvelle plateforme de messagerie DevOps !", now - timedelta(days=14), 'root', 'john_user'),
        ("Merci ! Belle interface. Comment puis-je configurer mon profil ?", now - timedelta(days=13), 'john_user', 'root'),
        ("Rends-toi dans les paramètres du compte, lien en haut à droite.", now - timedelta(days=13, hours=2), 'root', 'john_user'),
        ("Parfait, j'ai trouvé. Merci !", now - timedelta(days=12), 'john_user', None),
        ("Nouvelle version du déploiement disponible en préprod.", now - timedelta(days=10), 'alice_admin', 'root'),
        ("Je check ça et je te fais un retour.", now - timedelta(days=9), 'root', 'alice_admin'),
        ("Tout est OK, tu peux déployer en prod.", now - timedelta(days=8), 'root', 'alice_admin'),
        ("Déploiement effectué avec succès !", now - timedelta(days=7), 'alice_admin', 'root'),
        ("Bonjour, j'ai un souci d'accès à la base de données.", now - timedelta(days=6), 'bob_user', 'sarah_tech'),
        ("Peux-tu me donner plus de détails ? Quelle erreur vois-tu ?", now - timedelta(days=6, hours=3), 'sarah_tech', 'bob_user'),
        ("Erreur 'connection refused' sur le port 5432.", now - timedelta(days=5), 'bob_user', 'sarah_tech'),
        ("Vérifie que le service postgres est bien démarré : `systemctl status postgresql`", now - timedelta(days=5, hours=2), 'sarah_tech', 'bob_user'),
        ("C'était ça, merci ! Problème résolu.", now - timedelta(days=4), 'bob_user', 'sarah_tech'),
        ("Réunion technique demain 14h00 pour le sprint planning.", now - timedelta(days=3), 'alice_admin', 'john_user'),
        ("Présent. J'ai préparé les points sur l'API REST.", now - timedelta(days=3, hours=1), 'john_user', 'alice_admin'),
        ("Maintenance prévue ce week-end de 02h00 à 04h00.", now - timedelta(days=1), 'root', None),
        ("Nouveau tutoriel : comment utiliser l'API avec Swagger.", now - timedelta(hours=12), 'sarah_tech', 'bob_user'),
        ("Super, je vais regarder ça aujourd'hui.", now - timedelta(hours=6), 'bob_user', 'sarah_tech'),
        ("Rappel : penser à mettre à jour les variables d'env en prod.", now - timedelta(hours=3), 'root', 'alice_admin'),
        ("C'est noté, je fais ça cette après-midi.", now - timedelta(hours=1), 'alice_admin', 'root'),
    ]

    messages = []
    for contenu, date, owner_key, recipient_key in content_data:
        owner = users[owner_key]
        recipient = users[recipient_key] if recipient_key else None
        msg = Message.objects.create(
            contenu=contenu,
            date_envoi=date,
            owner=owner,
            recipient=recipient,
            is_read=True,
        )
        messages.append(msg)

    # Messages with MULTIPLE recipients
    multi_msgs = [
        ("Annonce : Nouvelle charte graphique disponible pour tous les projets.",
         now - timedelta(days=11), 'root', ['john_user', 'alice_admin', 'bob_user', 'sarah_tech']),
        ("Invitation à l'afterwork DevOps vendredi à 18h00.",
         now - timedelta(hours=48), 'alice_admin', ['john_user', 'bob_user', 'sarah_tech']),
        ("Rappel : Mercredi c'est pâtisserie ! Amenez vos spécialités.",
         now - timedelta(hours=24), 'bob_user', ['root', 'alice_admin', 'sarah_tech']),
    ]
    for contenu, date, owner_key, recipient_keys in multi_msgs:
        owner = users[owner_key]
        msg = Message.objects.create(
            contenu=contenu,
            date_envoi=date,
            owner=owner,
            is_read=False,
        )
        msg.recipients.set([users[k] for k in recipient_keys])
        msg.save()

    # Mark a few messages as unread
    for m in Message.objects.filter(recipient__isnull=False).order_by('-date_envoi')[:3]:
        m.is_read = False
        m.save()

    # Create threaded replies
    parent = Message.objects.order_by('date_envoi').first()
    if parent:
        reply = Message.objects.create(
            contenu="Suite à ce message, bienvenue à tous les nouveaux arrivants !",
            date_envoi=parent.date_envoi + timedelta(hours=1),
            owner=users['alice_admin'],
            recipient=parent.owner,
            parent=parent,
            is_read=True,
        )
        Message.objects.create(
            contenu="Merci Alice ! Hâte de collaborer avec l'équipe.",
            date_envoi=reply.date_envoi + timedelta(hours=2),
            owner=users['john_user'],
            recipient=reply.owner,
            parent=reply,
            is_read=False,
        )

    total = Message.objects.count()
    unread = Message.objects.filter(is_read=False).count()
    multi = Message.objects.exclude(recipients=None).count()
    print(f"  Created {total} messages ({unread} unread, {multi} multi-recipients)")


def run():
    print("=== Seed Data ===")
    clean()
    users = create_users()
    create_messages(users)
    print("=== Done ===")


if __name__ == '__main__':
    run()
