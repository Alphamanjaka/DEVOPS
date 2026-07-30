import logging

from django.http import HttpResponse
from django.db import connection
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


def health_check(request):
    logger.info("health_check called")
    try:
        connection.cursor()
        logger.info("health_check OK")
        return HttpResponse("OK", status=200)
    except Exception as e:
        logger.error("health_check failed: %s", e)
        return HttpResponse("Service Unavailable", status=503)


class LoginViewWithLogging(LoginView):
    def form_valid(self, form):
        logger.info("Login success: username=%s", form.cleaned_data.get('username'))
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.warning("Login failed: username=%s errors=%s",
                       form.cleaned_data.get('username', 'unknown'),
                       form.errors.as_text())
        return super().form_invalid(form)


def logout_view(request):
    username = request.user.username if request.user.is_authenticated else 'anonymous'
    logger.info("Logout: username=%s", username)
    logout(request)
    return redirect('login')


def error_400(request, exception=None):
    logger.error("Error 400: path=%s user=%s", request.path, request.user)
    return HttpResponse("Requête invalide", status=400)


def error_403(request, exception=None):
    logger.warning("Error 403: path=%s user=%s", request.path, request.user)
    return HttpResponse("Accès refusé", status=403)


def error_404(request, exception=None):
    logger.warning("Error 404: path=%s user=%s", request.path, request.user)
    return HttpResponse("Page non trouvée", status=404)


def error_500(request):
    logger.error("Error 500: path=%s user=%s method=%s",
                 request.path, request.user, request.method)
    return HttpResponse("Erreur interne du serveur", status=500)
