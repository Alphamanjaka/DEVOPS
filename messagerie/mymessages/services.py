import csv
import io
import logging

from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Count
from django.db.models.functions import TruncDay
from django.utils import timezone

from .models import Message

logger = logging.getLogger(__name__)


def get_message_stats():
    logger.info("get_message_stats called")
    daily_stats = Message.objects.annotate(
        date=TruncDay('date_envoi')
    ).values('date').annotate(count=Count('id')).order_by('date')
    labels = [s['date'].strftime('%d/%m/%Y') for s in daily_stats if s['date']]
    data = [s['count'] for s in daily_stats if s['date']]
    user_stats = Message.objects.values('owner__username').annotate(
        count=Count('id')).order_by('-count')
    user_labels = [s['owner__username'] or 'Anonyme' for s in user_stats]
    user_data = [s['count'] for s in user_stats]
    logger.info("get_message_stats: %d days, %d users", len(labels), len(user_labels))
    return {'labels': labels, 'data': data, 'user_labels': user_labels, 'user_data': user_data}


class MessageImportService:
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def import_csv(self, csv_file):
        logger.info("import_csv called, file size: %d", csv_file.size)
        if csv_file.size > self.MAX_FILE_SIZE:
            logger.error("import_csv: file too large (%d)", csv_file.size)
            raise ValueError("Le fichier dépasse la taille maximale de 10 Mo.")

        reader = csv.reader(io.TextIOWrapper(csv_file, encoding='utf-8'))

        success_count = 0
        error_count = 0

        for i, row in enumerate(reader):
            if not row:
                continue
            try:
                user = User.objects.get(username=row[2])
                recipient = None
                if len(row) > 3 and row[3]:
                    recipient = User.objects.filter(username=row[3]).first()

                raw_date = row[1]
                try:
                    parsed = datetime.fromisoformat(raw_date)
                except (ValueError, TypeError):
                    parsed = datetime.strptime(raw_date, '%Y-%m-%d')
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed)

                Message.objects.create(
                    contenu=row[0], date_envoi=parsed, owner=user, recipient=recipient)
                success_count += 1
            except (User.DoesNotExist, IndexError, Exception) as e:
                logger.warning("import_csv row %d error: %s", i, e)
                error_count += 1

        logger.info("import_csv done: %d success, %d errors", success_count, error_count)
        return success_count, error_count
