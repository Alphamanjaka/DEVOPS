import csv
from datetime import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Message


class MessageImportService:
    def import_csv(self, csv_file):
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)

        success_count = 0
        error_count = 0

        for row in reader:
            if row:
                try:
                    user = User.objects.get(username=row[2])
                    recipient = None
                    if len(row) > 3 and row[3]:
                        recipient = User.objects.filter(
                            username=row[3]).first()

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
                except (User.DoesNotExist, IndexError, Exception):
                    error_count += 1

        return success_count, error_count
