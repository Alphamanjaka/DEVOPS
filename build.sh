#!/bin/sh
set -e

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

# Attendre que la base de données soit joignable
log "Waiting for database..."
RETRIES=30
i=0
until python -c "
import os, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'messagerie.settings')
import django; django.setup()
from django.db import connection
connection.ensure_connection()
sys.exit(0)
" 2>/dev/null; do
  i=$((i + 1))
  if [ $i -ge $RETRIES ]; then
    log "ERROR: Database not reachable after $RETRIES attempts (host: $(python -c "import os; print(os.environ.get('DB_HOST', os.environ.get('DATABASE_URL', '?')))" 2>/dev/null || echo 'unknown'))"
    log "WARNING: Starting without database – app will be in degraded mode."
    break
  fi
  log "Database not ready yet (attempt $i/$RETRIES)..."
  sleep 2
done

if [ $i -lt $RETRIES ]; then
  log "Database is reachable."

  # Appliquer les migrations
  log "Applying database migrations..."
  python manage.py migrate --noinput

  # Créer un superutilisateur par défaut si nécessaire
  log "Creating default superuser..."
  python manage.py createsuperuser --no-input || true
else
  log "Skipping migrations and superuser creation (database unavailable)."
fi

# Collecter les fichiers statiques (ne nécessite pas de base)
log "Collecting static files..."
python manage.py collectstatic --noinput

# Lancer Gunicorn avec Uvicorn worker (ASGI)
log "Starting Gunicorn with Uvicorn worker..."
exec gunicorn --bind 0.0.0.0:8000 --reload -k uvicorn.workers.UvicornWorker messagerie.asgi:application
