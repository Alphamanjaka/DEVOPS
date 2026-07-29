from django.urls import path
from mymessages.webhook_views import github_webhook

urlpatterns = [
    path('github/', github_webhook, name='github_webhook'),
]
