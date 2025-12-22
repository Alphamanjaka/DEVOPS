FROM python:3.12-slim

WORKDIR /app

# On copie tout le contenu du dossier actuel
COPY . .

RUN pip install --no-cache-dir django

# On force Docker à nous dire où il est et ce qu'il voit (utile pour débugger)
RUN ls -la

# IMPORTANT : On change le dossier de travail pour aller là où se trouve manage.py
WORKDIR /app/messagerie

# Lancement des tests
CMD ["python", "manage.py", "test"]