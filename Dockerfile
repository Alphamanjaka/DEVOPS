# 1. Utiliser une image Python légère
FROM python:3.10-slim

# 2. Définir le dossier de travail
WORKDIR /app

# 3. Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copier le reste du projet
COPY . .

# 5. Lancer les tests par défaut (utile pour la CI)
CMD ["python", "manage.py", "test"]