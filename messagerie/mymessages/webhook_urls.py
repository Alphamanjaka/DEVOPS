from django.urls import path
from mymessages.views import github_webhook

urlpatterns = [
    path('github/', github_webhook, name='github_webhook'),
]
