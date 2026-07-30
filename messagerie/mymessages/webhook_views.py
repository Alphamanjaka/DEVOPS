import hashlib
import hmac
import json
import os

from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Message


def _get_bot_user():
    bot, _ = User.objects.get_or_create(
        username='github-bot',
        defaults={'is_active': True},
    )
    return bot


@csrf_exempt
def github_webhook(request):
    if request.method == 'GET':
        return JsonResponse({'message': 'Webhook GitHub: utilisez POST avec un payload GitHub.'})
    secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
    if not secret:
        return HttpResponse('GITHUB_WEBHOOK_SECRET not configured', status=500)

    body = request.body
    signature = request.META.get('HTTP_X_HUB_SIGNATURE_256', '')
    expected = 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return HttpResponse(status=401)

    event = request.META.get('HTTP_X_GITHUB_EVENT', 'push')
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if event == 'push':
        ref = payload.get('ref', '')
        branch = ref.replace('refs/heads/', '')
        commits = payload.get('commits', [])
        repo_name = payload.get('repository', {}).get('full_name', 'unknown')
        pusher = payload.get('pusher', {}).get('name', 'unknown')
        commit_count = len(commits)
        body_text = (
            f"[GitHub] Push sur {repo_name}/{branch} par {pusher}\n"
            f"{commit_count} commit(s) envoyé(s)"
        )
        if commits:
            c = commits[-1]
            body_text += f"\nDernier commit: {c.get('id', '')[:7]} - {c.get('message', '')}"
    elif event == 'pull_request':
        pr = payload.get('pull_request', {})
        action = payload.get('action', 'unknown')
        repo_name = payload.get('repository', {}).get('full_name', 'unknown')
        body_text = (
            f"[GitHub] PR {action} - {repo_name}#{pr.get('number', '')}\n"
            f"Titre: {pr.get('title', '')}\n"
            f"Auteur: {pr.get('user', {}).get('login', 'unknown')}\n"
            f"URL: {pr.get('html_url', '')}"
        )
    else:
        body_text = f"[GitHub] Événement: {event}\n{json.dumps(payload, indent=2)[:2000]}"

    bot = _get_bot_user()
    active_users = User.objects.filter(is_active=True)
    Message.objects.bulk_create([
        Message(contenu=body_text, owner=bot, recipient=user)
        for user in active_users
    ])

    return JsonResponse({'status': 'ok', 'notified': active_users.count()})
