# Utiliser une image Python officielle légère
FROM python:3.12-slim

# Définir des variables d'environnement pour Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les dépendances et les installer
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
# --- ÉTAPE CRUCIALE POUR RENDER ---
# On prépare les fichiers statiques pour éviter les erreurs au démarrage
RUN python manage.py collectstatic --noinput
# Copier le reste du projet
COPY . /app/

# Se placer dans le dossier du projet Django (là où se trouve wsgi.py/manage.py)
WORKDIR /app/messagerie

# Commande par défaut pour lancer Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "messagerie.wsgi:application"]