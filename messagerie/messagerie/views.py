from django.http import HttpResponse
from django.db import connection


def health_check(request):
    try:
        # On tente une requête ultra-simple sur la base
        connection.cursor()
        return HttpResponse("OK", status=200)
    except Exception:
        return HttpResponse("Service Unavailable", status=503)
