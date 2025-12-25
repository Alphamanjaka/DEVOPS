#!/bin/sh

# Ce script est exécuté par le conteneur 'web' au démarrage.

# Appliquer les migrations de la base de données
echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Créer un superutilisateur par défaut si nécessaire
echo "Creating default superuser..."
python manage.py createsuperuser --no-input || true

# Lancer Gunicorn pour servir l'application
echo "Starting Gunicorn..."
gunicorn --bind 0.0.0.0:8000 --reload messagerie.wsgi:application