from django.db import connection


def db_health_check():
    try:
        connection.cursor()
        return True
    except Exception:
        return False
