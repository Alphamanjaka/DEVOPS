FROM python:3.12-slim

# Empêche Python de générer des fichiers .pyc et permet l'affichage des logs en direct
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copier d'abord le fichier des dépendances pour utiliser le cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie de tout le projet
COPY . .

# On se place là où se trouve manage.py
WORKDIR /app/messagerie

# Le port doit correspondre à celui dans docker-compose.yml
EXPOSE 8000

# Commande de démarrage pour Render (utilise le script build.sh)
CMD ["sh", "/app/build.sh"]