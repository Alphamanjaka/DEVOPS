# Présentation 8 min — Messagerie DevOps

**Format :** Slides uniquement (sans démo live) — screenshots intégrés dans les slides.
**Déployé :** https://devops-omjy.onrender.com
**Fil conducteur :** le DevOps **d'abord** — l'application de messagerie est le *support* qui démontre le pipeline (elle joue le rôle du « produit livré »).

Message à retenir : **« du commit au déploiement, tout est automatisé, vérifié et sécurisé — sans intervention manuelle. »**

---

## Plan d'ensemble (8 min)

| # | Slide | Timing | Durée | Message clé |
|---|---|---|---|---|
| 1 | Contexte & objectif DevOps | 0:00 – 0:40 | 40s | Livrer une app en continu : automatisé, vérifié, sécurisé |
| 2 | L'application — support du pipeline | 0:40 – 1:20 | 40s | Le produit qui traverse le pipeline (temps réel) |
| 3 | Conteneurisation (Docker) | 1:20 – 2:10 | 50s | Image multi-stage + orchestration Compose = env reproductible |
| 4 | **Pipeline CI/CD (cœur)** | 2:10 – 3:40 | 1min30 | Tests → lint → sécurité → build → push → deploy |
| 5 | Sécurité | 3:40 – 4:40 | 1min | Trivy bloquant, pre-commit, Dependabot, durcissement |
| 6 | Qualité & testabilité | 4:40 – 5:30 | 50s | 94% coverage, health check, logging, gestion d'erreurs |
| 7 | Déploiement & monitoring | 5:30 – 6:20 | 50s | Render + webhook + version du commit exposée |
| 8 | Difficultés + conclusion | 6:20 – 8:00 | 1min40 | 3 problèmes résolus par l'approche DevOps + bilan |

*Timing total ≈ 7min20 → 40s de marge pour les questions et les aléas.*

---

## Slide 1 — Contexte & objectif DevOps (0:00 → 0:40)

**Contenu de la slide :**
- Titre : « Messagerie — une application livrée par un pipeline DevOps de bout en bout »
- Le défi affiché : *code → test → sécuriser → build → déployer, automatiquement, à chaque commit*
- Badges : Docker · GitHub Actions · Trivy · PostgreSQL · Django · Python 3.12
- Screenshot du pipeline GitHub Actions (jobs verts)

**Texte à dire (≈40s) :**
> « Je vais vous présenter une application Django de messagerie, mais le sujet de cette présentation, c'est avant tout le **DevOps** : comment ce produit est développé, testé, sécurisé, conteneurisé et déployé automatiquement.
> L'idée est simple : à chaque commit, le code doit passer toute une chaîne de contrôles — tests, qualité, sécurité — puis être livré en production sans aucune intervention manuelle. Et si un seul contrôle échoue, rien ne part. »

**Transition :** « D'abord, de quoi on parle : le produit. »

---

## Slide 2 — L'application, support du pipeline (0:40 → 1:20)

**Contenu de la slide :** screenshot de l'app + 3 bullets
- Messagerie Django : CRUD, read/unread, threads, recherche, import CSV / export PDF
- **Temps réel WebSocket** (Django Channels) : notifications instantanées, toasts, badge, reconnexion auto
- Son rôle : un **banc d'essai réaliste** pour le pipeline (base de données, migrations, webhooks, temps réel)

**Texte à dire (≈40s) :**
> « Le produit lui-même est une messagerie complète : gestion de messages, fil de discussion, recherche, import et export, et même une fonctionnalité temps réel avec Django Channels — les notifications arrivent sans recharger la page.
> Mais je ne vais pas m'attarder dessus. Cette application nous intéresse parce qu'elle est un **banc d'essai réaliste** : elle a une base de données, des migrations, des dépendances, une partie temps réel, des webhooks. Autant de contraintes qu'un vrai pipeline DevOps doit gérer. »

**Transition :** « La première étape de la démarche, c'est la conteneurisation. »

---

## Slide 3 — Conteneurisation (1:20 → 2:10)

**Contenu de la slide :**
- Schéma : `Dockerfile multi-stage` → image applicative | `docker-compose.yml` → web + db + redis
- Point clé : **cache Docker** — les dépendances installées avant le code → builds rapides
- Environnement identique partout : local (Windows/Mac) = CI = production
- Screenshot des couches de build

**Texte à dire (≈50s) :**
> « Tout est conteneurisé. Le Dockerfile est **multi-stage** : on compile les dépendances dans un premier environnement, puis on ne copie dans l'image finale que le strict nécessaire — une image plus petite, donc plus sûre.
> L'ordre des instructions est pensé pour le **cache Docker** : les dépendances sont installées avant la copie du code, ce qui accélère fortement les builds en CI.
> Docker Compose orchestre trois services : l'application, PostgreSQL et Redis pour le temps réel.
> Le résultat, c'est un environnement **reproductible** : exactement le même conteneur tourne sur la machine du développeur, dans la CI et en production. C'est la base de toute la suite. »

**Transition :** « Avec cette image, on peut construire le cœur du dispositif : le pipeline. »

---

## Slide 4 — Pipeline CI/CD — le cœur (2:10 → 3:40)

**Contenu de la slide :** diagramme du pipeline
```
Push / PR → ① tests  → ② lint  → ③ security (Trivy)
                        ↓   (tout est vert)
                     build → push GHCR → deploy Render → health check
```
- Détails des jobs (tableau) : déclencheur, rôle
- Webhook GitHub → `/api/webhook/github/` → l'app se fait notifier de son propre déploiement
- Screenshot des jobs verts dans GitHub Actions

**Texte à dire (≈1min30) :**
> « Voici le cœur du projet : le pipeline GitHub Actions.
> À chaque push ou pull request, trois contrôles s'exécutent **en parallèle**. Les tests unitaires d'abord, avec le seuil de couverture. Le lint, via pre-commit. Et le scan de sécurité de l'image Docker avec Trivy. Ces trois jobs sont **bloquants** : le pipeline s'arrête si l'un d'eux échoue.
> Sur la branche main uniquement, quand tout est vert, l'image est construite, publiée dans le registre GitHub, puis déployée automatiquement sur Render.
> Et la boucle se referme : après déploiement, GitHub notifie l'application elle-même via un webhook signé — c'est l'application qui reçoit la confirmation de sa propre mise en production, et un health check confirme que la base de données répond.
> Le point essentiel : **aucune intervention manuelle** entre le commit et la mise en production. »

**Transition :** « Mais un pipeline sans sécurité, ce n'est pas du DevOps. »

---

## Slide 5 — Sécurité (3:40 → 4:40)

**Contenu de la slide :** 4 tuiles
- **Trivy** : scanne l'image (OS + Python), bloque HIGH/CRITICAL (exit-code 1), rapport SARIF dans GitHub Security tab
- **Pre-commit** : détection de secrets privés, fichiers YAML/JSON invalides, code de debug
- **Dependabot** : mises à jour automatiques hebdomadaires (pip, Docker, Actions)
- **Durcissement Django en prod** : HTTPS forcé, HSTS, cookies de session et CSRF sécurisés
- Screenshot du rapport SARIF / Security tab

**Texte à dire (≈1min) :**
> « La sécurité est intégrée à chaque étage du pipeline.
> À l'entrée, pre-commit empêche de committer des secrets ou du code de debug. Les dépendances sont mises à jour automatiquement chaque semaine par Dependabot.
> Le plus important, c'est Trivy : à chaque push, il scanne l'image Docker — le système d'exploitation et les librairies Python — et **bloque le pipeline dès qu'une vulnérabilité haute ou critique est détectée**. Le rapport est aussi importé dans l'onglet Security de GitHub pour le suivi.
> Enfin, la configuration de production applique le durcissement Django : HTTPS forcé, HSTS, cookies sécurisés.
> Résultat : une vulnérabilité critique ne peut **jamais** arriver en production. »

**Transition :** « À la sécurité s'ajoute la vérification permanente de la qualité. »

---

## Slide 6 — Qualité & testabilité (4:40 → 5:30)

**Contenu de la slide :** 4 tuiles
- **Tests** : 34 tests, **94% de couverture** (seuil 70%)
- **Health check** `/health/` : JSON structuré (statut, version du commit, état DB) — 200/503
- **Seed data** : jeu de données rejoué dans la CI pour valider le pipeline de données complet
- **Logging structuré** + pages d'erreur 400/403/404/500 avec contexte
- Screenshot de la réponse `/health/`

**Texte à dire (≈50s) :**
> « La qualité est vérifiée en continu, pas seulement au moment de la livraison.
> Trente-quatre tests couvrent le code à quatre-vingt-quatorze pour cent. La CI **rejoue aussi le jeu de données de démarrage** après les migrations, pour valider que toute la chaîne — migrations, seed, application — fonctionne en environnement réel.
> Une fois en production, un endpoint de health check expose un JSON structuré : l'état de la base de données et la **version exacte du commit déployé**. C'est ce que consomment des outils de monitoring comme UptimeRobot.
> Et pour diagnostiquer, chaque erreur — 400, 403, 404, 500 — est loguée avec le contexte, avec des pages d'erreur personnalisées. »

**Transition :** « Parlons justement du déploiement en conditions réelles. »

---

## Slide 7 — Déploiement & monitoring (5:30 → 6:20)

**Contenu de la slide :** schéma de boucle
- GitHub → GHCR → Render (déploiement auto via webhook)
- PostgreSQL managé + Redis (fallback InMemory en dev)
- Script de démarrage robuste : attente de la DB, migrations, superuser, collectstatic, Gunicorn/Uvicorn (ASGI)
- `/health/` consommé par les outils de monitoring
- Screenshot de l'app en production

**Texte à dire (≈50s) :**
> « En production, l'application tourne sur Render avec PostgreSQL managé. La base est **attendant prête** par le script de démarrage avant que les migrations ne soient appliquées — un des points classiques d'échec de déploiement.
> Le script enchaîne : attente de la base, migrations, création du superutilisateur, collecte des fichiers statiques, puis démarrage de Gunicorn en mode ASGI pour supporter le temps réel.
> Le health check rend chaque déploiement **observable** : on connaît à tout moment le statut de l'application et le commit déployé, ce qui rend le monitoring et le débogage beaucoup plus simples. »

**Transition :** « Enfin, les difficultés réelles — et comment l'approche DevOps a aidé à les surmonter. »

---

## Slide 8 — Difficultés + Conclusion (6:20 → 8:00)

**Contenu de la slide :**
- 3 difficultés techniques (format avant/après) :
  1. **ASGI** : `get_asgi_application()` avant l'import du routing, sinon `ImproperlyConfigured`
  2. **Sync/async (Channels 4)** : `group_send` asynchrone → `async_to_sync` depuis les signaux Django
  3. **Ordre des signaux** : destinataires M2M pas encore enregistrés dans `post_save` → signal `m2m_changed`
- Chaque bug détecté et corrigé *grâce aux logs structurés et à la CI* → argument DevOps
- **Bilan** : du commit au déploiement, tout est automatisé, vérifié, sécurisé
- **Perspectives** : Redis managé, tests e2e (Playwright), rollback automatisé, monitoring/alerting
- « Merci — questions ? »

**Texte à dire (≈1min40) :**
> « Pour finir, trois difficultés réelles, et comment elles illustrent la valeur du DevOps.
> Premièrement, l'initialisation ASGI : le moindre problème d'ordre de chargement faisait échouer l'application au démarrage — détecté immédiatement par les tests de la CI. Deuxièmement, un piège de Django Channels 4 : les opérations temps réel sont asynchrones, et appelées depuis un signal elles n'étaient jamais exécutées. Le correctif, `async_to_sync`, a été validé par l'observation des logs structurés en production. Troisièmement, l'ordre des signaux lors d'un envoi à plusieurs destinataires, résolu avec un signal `m2m_changed`.
> Le point commun : **aucun de ces bugs n'est passé en production sans être visible, tracé et corrigé** — c'est exactement ce que doit apporter une démarche DevOps : de la visibilité et de l'automatisation.
> En résumé : un produit livré à chaque commit, de façon reproductible, vérifiée et sécurisée. Les perspectives : un Redis managé, des tests de bout en bout, et un rollback automatisé.
> Merci, je vous écoute. »

---

## Check-list avant la présentation

- [ ] Vérifier que https://devops-omjy.onrender.com/health/ répond `"status": "ok"`
- [ ] Screenshots à jour : pipeline GitHub Actions (3 jobs verts + build-and-push), rapport SARIF/Trivy, réponse `/health/` (version + db), Dockerfile multi-stage (couches), Docker Compose, app en production
- [ ] Répéter le timing : script total ≈ 7min20 ; marge de 40s pour les questions
- [ ] Avoir le repo ouvert sur le dernier commit (WebSocket) pour les questions techniques
- [ ] Questions probables du jury — réponses prêtes :
  - *« Pourquoi Docker multi-stage ? »* → image finale plus petite, couche build séparée des dépendances, moins de surface d'attaque
  - *« Que bloque le pipeline si un test échoue ? »* → le job build-and-push ne démarre pas, aucune image publiée, pas de déploiement
  - *« Comment Trivy bloque-t-il ? »* → exit-code 1 si vulnérabilité HIGH/CRITICAL → job en échec → pipeline bloqué + rapport SARIF uploadé
  - *« Comment connaît-on la version déployée ? »* → `/health/` renvoie `version` = 7 premiers chars du commit (variable `RENDER_GIT_COMMIT`)
  - *« Pourquoi le webhook GitHub ? »* → l'application reçoit la confirmation de son propre déploiement (HMAC signé), boucle CI/CD ↔ produit fermée
