FROM python:3.12-slim AS builder

WORKDIR /app

# On installe les dépendances nécessaires à la compilation si besoin
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev

# Copier d'abord le fichier des dépendances pour utiliser le cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- STAGE 2 : FINAL ---
FROM python:3.12-slim
# Copie de tout le projet
WORKDIR /app

# On récupère uniquement les bibliothèques installées du stage builder
COPY --from=builder /root/.local /root/.local
COPY . .

# Mise à jour du PATH pour trouver les bibliothèques copiées
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# On se place là où se trouve manage.py
WORKDIR /app/messagerie

# Le port doit correspondre à celui dans docker-compose.yml
EXPOSE 8000

# Commande de démarrage pour Render (utilise le script build.sh)
CMD ["sh", "/app/build.sh"]