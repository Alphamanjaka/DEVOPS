import hashlib
import hmac
import json
import os

from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Message


@csrf_exempt
@require_POST
def github_webhook(request):
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET', '')

    body = request.body
    signature = request.META.get('HTTP_X_HUB_SIGNATURE_256', '')
    if secret:
        expected = 'sha256=' + hmac.new(
            secret.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return HttpResponse(status=401)

    event = request.META.get('HTTP_X_GITHUB_EVENT', 'push')
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    active_users = User.objects.filter(is_active=True)
    if event == 'push':
        ref = payload.get('ref', '')
        branch = ref.replace('refs/heads/', '')
        commits = payload.get('commits', [])
        repo_name = payload.get('repository', {}).get('full_name', 'unknown')
        pusher = payload.get('pusher', {}).get('name', 'unknown')
        commit_count = len(commits)
        subject = f"[GitHub] Push sur {repo_name}/{branch}"
        body = (
            f"Nouveau push sur {repo_name}/{branch} par {pusher}\n"
            f"{commit_count} commit(s) envoyé(s)"
        )
        if commits:
            body += "\n\nDernier commit:"
            c = commits[-1]
            body += f"\n  {c.get('id', '')[:7]} - {c.get('message', '')}"
    elif event == 'pull_request':
        pr = payload.get('pull_request', {})
        action = payload.get('action', 'unknown')
        repo_name = payload.get('repository', {}).get('full_name', 'unknown')
        pr_title = pr.get('title', '')
        pr_url = pr.get('html_url', '')
        pr_user = pr.get('user', {}).get('login', 'unknown')
        subject = f"[GitHub] PR {action} - {repo_name}#{pr.get('number', '')}"
        body = (
            f"Pull Request {action} sur {repo_name}\n"
            f"Titre: {pr_title}\n"
            f"Auteur: {pr_user}\n"
            f"URL: {pr_url}"
        )
    else:
        subject = f"[GitHub] Événement: {event}"
        body = json.dumps(payload, indent=2)[:2000]

    for user in active_users:
        Message.objects.create(
            contenu=body,
            subject=subject,
            owner=user,
            recipient=user,
        )

    return JsonResponse({'status': 'ok', 'notified': active_users.count()})