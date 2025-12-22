FROM python:3.12-slim

WORKDIR /app

# On installe les dépendances
RUN pip install --no-cache-dir django

# On copie tout le projet
COPY . .

# On se déplace là où se trouve manage.py
WORKDIR /app/messagerie

# --- ÉTAPE CRUCIALE POUR RENDER ---
# On prépare les fichiers statiques pour éviter les erreurs au démarrage
RUN python manage.py collectstatic --noinput

# On lance le serveur sur le port 10000 (standard chez Render)
CMD ["python", "manage.py", "runserver", "0.0.0.0:10000"]