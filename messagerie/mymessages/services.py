import csv
from django.contrib.auth.models import User
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

                    Message.objects.create(
                        contenu=row[0], date_envoi=row[1], owner=user, recipient=recipient)
                    success_count += 1
                except (User.DoesNotExist, IndexError, Exception):
                    error_count += 1

        return success_count, error_count
