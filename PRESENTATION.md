# Présentation 8 min — GitHub Actions comme outil DevOps

**Format :** Slides uniquement (sans démo live) — screenshots intégrés dans les slides.
**Sujet :** **GitHub Actions** en tant qu'outil DevOps — son fonctionnement, ses concepts, ses forces et ses limites.
**Cas d'usage :** le projet *Messagerie* (Django) traverse le pipeline comme démonstration concrète.
**Déployé :** https://devops-omjy.onrender.com

Fil conducteur : **« Un seul fichier YAML dans le dépôt transforme chaque commit en livraison testée, sécurisée et automatisée. »**

---

## Plan d'ensemble (8 min)

| # | Slide | Timing | Durée | Message clé |
|---|---|---|---|---|
| 1 | Le besoin & le choix de l'outil | 0:00 – 0:40 | 40s | Pourquoi un outil CI/CD, pourquoi GitHub Actions |
| 2 | GitHub Actions : les concepts | 0:40 – 2:00 | 1min20 | Workflow YAML, triggers, jobs, steps, actions |
| 3 | Notre pipeline en pratique | 2:00 – 3:30 | 1min30 | Le `ci.yml` réel appliqué au projet |
| 4 | Une exécution en images | 3:30 – 4:30 | 1min | Jobs verts, logs, artifacts, rapports |
| 5 | Sécurité & qualité intégrées | 4:30 – 5:30 | 1min | Trivy, PR checks, secrets, Dependabot |
| 6 | Forces & limites de l'outil | 5:30 – 6:30 | 1min | Ce qu'il apporte vs ses limites |
| 7 | Retour d'expérience | 6:30 – 7:30 | 1min | 3 bugs réels détectés par la CI |
| 8 | Conclusion + questions | 7:30 – 8:00 | 30s | Bilan et perspectives |

---

## Slide 1 — Le besoin & le choix de l'outil (0:00 → 0:40)

**Contenu de la slide :**
- Titre : « GitHub Actions — la CI/CD au cœur du dépôt »
- Le besoin : *intégrer, tester, sécuriser et livrer le code automatiquement à chaque commit*
- Pourquoi GitHub Actions :
  - Déjà intégré au dépôt (zéro serveur à installer, zéro config Jenkins à maintenir)
  - Pas d'infrastructure à héberger (runners hébergés par GitHub)
  - Configuration par code (workflow-as-code en YAML)
- Screenshot de l'onglet Actions du repo

**Texte à dire (≈40s) :**
> « Pour automatiser la livraison du projet, il fallait un outil de CI/CD. J'ai retenu **GitHub Actions**.
> Son avantage décisif : tout est déclaré dans le dépôt, sous forme de code. Aucun serveur à installer — les jobs s'exécutent sur des machines hébergées par GitHub — et le résultat s'affiche directement dans l'onglet Actions du dépôt.
> La promesse : à chaque commit, le code est automatiquement testé, contrôlé, sécurisé, puis livré. Je vais d'abord expliquer les concepts de l'outil, puis montrer comment il est utilisé sur le projet. »

**Transition :** « Voyons les briques de GitHub Actions. »

---

## Slide 2 — GitHub Actions : les concepts (0:40 → 2:00)

**Contenu de la slide :** schéma conceptuel
```
Workflow (.github/workflows/ci.yml)
 ├─ on:          → déclencheurs (push, pull_request)
 ├─ jobs:        → exécutés sur des runners (ubuntu-latest)
 │   ├─ steps    → actions réutilisables (Marketplace) ou commandes
 │   ├─ needs    → dépendances entre jobs
 │   └─ if       → conditions
 └─ secrets / artifacts / env
```
- 5 mots-clés à retenir : **workflow, déclencheur, job, step, action**
- Screenshot d'un extrait YAML annoté

**Texte à dire (≈1min20) :**
> « GitHub Actions repose sur des fichiers YAML placés dans `.github/workflows/`. On appelle ça un **workflow**.
> Premier mot-clé : le **déclencheur**, la clause `on`. Le workflow peut démarrer sur un push, une pull request, un horaire — ou même manuellement. Dans notre cas : push sur main et develop, pull request vers main.
> Le workflow contient des **jobs**, chacun exécuté sur un **runner** — une machine Linux, Windows ou macOS hébergée par GitHub. Notre pipeline utilise `ubuntu-latest`.
> Chaque job est une liste d'étapes, les **steps** : soit des commandes directes, soit des **actions** réutilisables — comme `checkout`, qui récupère le code, ou `setup-python`. Ces actions viennent d'un **Marketplace**, un peu comme des modules.
> Deux mécanismes de contrôle : `needs`, pour exprimer qu'un job dépend des résultats d'un autre, et `if`, pour des conditions. Enfin, l'outil gère les **secrets**, les **artifacts** — des fichiers produits et téléchargeables — et l'**environnement global** du workflow. »

**Transition :** « Appliquons ces concepts au projet. »

---

## Slide 3 — Notre pipeline en pratique (2:00 → 3:30)

**Contenu de la slide :** le pipeline réel annoté (avec le YAML derrière)
```
push/PR ─▶ ① tests ─┐
                    ├─▶ ③ security (Trivy) ─▶ ④ build-and-push (main uniquement)
          ② lint  ──┘                                   └─▶ webhook notification
```
- Détails du job `tests` : .env de test → compose → migrations → coverage ≥70% → seed data → health check → artifact
- Détail du job `security` : `needs: [tests, lint]`, scan HIGH/CRITICAL, exit-code 1
- Détail du job `build-and-push` : `needs: [tests, lint, security]` + `if: main && push`, login GHCR avec `GITHUB_TOKEN`, tags `latest` + `sha`, webhook
- L'effet bloquant : un job rouge empêche le suivant

**Texte à dire (≈1min30) :**
> « Concrètement, le projet a un workflow unique nommé *CI/CD* avec quatre jobs.
> Le premier, **tests**, reproduit l'environnement complet : il construit l'image Docker, démarre PostgreSQL, applique les migrations, exécute les tests avec la couverture — bloquante dès quatre-vingt-dix pour cent — puis le jeu de données de démarrage et le health check. Le rapport de couverture est publié comme **artifact**, téléchargeable.
> Le deuxième, **lint**, lance pre-commit pour la qualité du code.
> Le job **security** ne démarre que si les deux premiers réussissent — c'est la directive `needs`. Il construit l'image et la scanne avec Trivy : toute vulnérabilité haute ou critique fait échouer le job.
> Enfin, **build-and-push** n'exécute que sur la branche main, grâce à `if`. Il se connecte au registre avec le secret `GITHUB_TOKEN`, publie l'image avec deux tags — `latest` et le hash du commit — puis notifie l'application via un webhook.
> Le principe fondamental : **un job qui échoue bloque toute la suite. Rien ne part en production. »**

**Transition :** « Regardons ce que ça donne concrètement. »

---

## Slide 4 — Une exécution en images (3:30 → 4:30)

**Contenu de la slide :** 4 screenshots côte à côte
- Liste des runs (jobs verts, badges ✓)
- Détail d'un run : arborescence tests / lint / security / build-and-push
- Logs d'une step (ex. migrations ou coverage)
- Artifact `coverage-report` + upload SARIF

**Texte à dire (≈1min) :**
> « En pratique, chaque commit produit une **exécution** visible dans l'onglet Actions : les quatre jobs s'affichent en parallèle puis se rejoignent, avec un statut vert ou rouge.
> On peut ouvrir chaque job pour voir le détail de ses étapes, chaque étape avec ses logs en temps réel — très utile pour comprendre un échec.
> Les **artifacts** permettent de récupérer les rapports : ici le rapport de couverture, et là le rapport SARIF de Trivy, automatiquement importé dans l'onglet Security de GitHub — la boucle est bouclée, l'outil CI alimente directement l'outil de suivi de sécurité.
> Pour le développeur, c'est un retour d'information immédiat : est-ce que mon code est correct ? Y a-t-il une vulnérabilité ? Suis-je bon pour la livraison ? »

**Transition :** « La sécurité fait partie intégrante de l'outil. »

---

## Slide 5 — Sécurité & qualité intégrées (4:30 → 5:30)

**Contenu de la slide :** 4 tuiles
- **PR checks** : les jobs bloquent le merge d'une pull request (statut requis)
- **Secrets** : `GITHUB_TOKEN` (rotation auto), variables `env` du workflow, jamais commitées
- **Trivy** : scan image OS + Python, `exit-code: 1` sur HIGH/CRITICAL, rapport SARIF dans GitHub Security
- **Dependabot** : PRs automatiques de mise à jour (pip, Docker, Actions) → passent aussi par le pipeline
- Screenshot : Security tab / dépendances / onglet Secrets

**Texte à dire (≈1min) :**
> « GitHub Actions ne se limite pas au pipeline : il s'articule avec toute la sécurité de la plateforme.
> Les **pull requests** sont bloquées tant que les jobs n'ont pas réussi — aucun code non validé ne peut être fusionné.
> Les **secrets**, comme le `GITHUB_TOKEN`, sont injectés au moment de l'exécution et ne sont jamais exposés dans les logs ou le code.
> Le scan Trivy est branché directement sur l'onglet Security, via le rapport SARIF : les vulnérabilités sont tracées au même endroit que le code.
> Et **Dependabot** ouvre automatiquement des pull requests de mise à jour de dépendances — qui passent elles-mêmes par le pipeline avant d'être fusionnées. La sécurité devient un flux continu, pas un contrôle ponctuel. »

**Transition :** « Après cette implémentation, quelles forces et quelles limites de l'outil ? »

---

## Slide 6 — Forces & limites de GitHub Actions (5:30 → 6:30)

**Contenu de la slide :** deux colonnes
- **Forces** : intégration native GitHub (PR, Security, secrets), écosystème Marketplace (Trivy, CodeQL, pre-commit…), workflow-as-code versionné avec le dépôt, aucun serveur à administrer, gratuit pour les repos publics, matrix pour les versions
- **Limites** : dépendance à l'écosystème GitHub (vendor lock-in), runners partagés (performances variables), coût sur les repos privés, temps de démarrage des jobs, YAML verbeux sur les gros pipelines

**Texte à dire (≈1min) :**
> « Qu'est-ce que cette expérience m'apprend sur l'outil ?
> Côté **forces** : l'intégration est native avec l'écosystème GitHub — pull requests, secrets, onglet Security. Le Marketplace fournit des actions prêtes à l'emploi, Trivy, CodeQL, pre-commit, qui évitent de tout réécrire. La configuration étant du code, elle est versionnée, revue et historisée avec le dépôt. Et surtout, aucun serveur à administrer.
> Côté **limites** : on devient dépendant de l'écosystème GitHub — un changement de plateforme imposerait de réécrire les workflows. Les runners sont partagés, les performances variables. Et sur un dépôt privé, le coût peut devenir significatif.
> Pour un projet comme celui-ci, les forces l'emportent largement. »

**Transition :** « Terminons par le retour d'expérience concret. »

---

## Slide 7 — Retour d'expérience (6:30 → 7:30)

**Contenu de la slide :** 3 bugs réels → comment la CI les a attrapés
1. **ASGI mal configuré** → l'app ne démarrait pas → attrapé par les tests du job `tests`
2. **Coroutine jamais exécutée** (Channels 4, `group_send` asynchrone) → détecté par les logs + vérifié en CI
3. **Ordre des signaux Django** (destinataires M2M absents au `post_save`) → détecté en testant l'envoi multiple, validé par le pipeline

**Texte à dire (≈1min) :**
> « L'intérêt de l'outil, on le mesure surtout quand ça casse.
> Premier bug : une configuration ASGI incorrecte faisait échouer l'application au démarrage. C'est le job de tests qui l'a détecté, à chaque commit, avant toute mise en production.
> Deuxième bug, plus subtil : en Django Channels 4, l'envoi temps réel est asynchrone ; appelé depuis un signal, le message n'était jamais envoyé. C'est l'observation des logs en production qui l'a révélé, puis le correctif a été validé par le pipeline.
> Troisième bug : lors d'un envoi à plusieurs destinataires, le signal se déclenchait avant l'enregistrement des destinataires. Résolu en écoutant le bon signal, et re-vérifié par la CI.
> Le point commun : **avec CI/CD, aucun de ces bugs n'a pu arriver en production sans être visible et contrôlé. C'est exactement la valeur de l'outil. »**

**Transition :** « Conclusion. »

---

## Slide 8 — Conclusion + questions (7:30 → 8:00)

**Contenu de la slide :**
- GitHub Actions = CI/CD intégrée au dépôt, workflow-as-code en YAML
- Bilan : 4 jobs, 3 contrôles bloquants, déploiement automatique, sécurité tracée
- Chiffres : 34 tests, 94% de couverture, Trivy HIGH/CRITICAL bloquant
- Perspectives : matrix des versions, déploiement multi-environnements, tests e2e dans le pipeline
- « Merci — questions ? »

**Texte à dire (≈30s) :**
> « Pour conclure : GitHub Actions est un outil DevOps complet, intégré au dépôt, qui automatise le cycle de vie du code — tests, qualité, sécurité et livraison — à partir d'un simple fichier YAML versionné.
> Sur ce projet, il livre un pipeline de quatre jobs aux contrôles bloquants, avec trente-quatre tests, quatre-vingt-quatorze pour cent de couverture et un scan de sécurité qui bloque toute vulnérabilité critique.
> Les perspectives : tester sur plusieurs versions, déployer sur plusieurs environnements, et intégrer des tests de bout en bout.
> Merci, je vous écoute. »

---

## Check-list avant la présentation

- [ ] Vérifier que https://devops-omjy.onrender.com/health/ répond `"status": "ok"`
- [ ] Screenshots à jour :
  - Onglet **Actions** : liste des runs + une exécution avec les 4 jobs verts
  - **YAML** du workflow annoté (extrait `ci.yml`)
  - **Logs** d'une step (ex. tests + coverage)
  - **Artifact** `coverage-report` + rapport **SARIF** dans Security tab
  - Onglet **Secrets** et onglet **Dependabot**
  - Branch protection : statuts requis sur les PR
- [ ] Répéter le timing : script ≈ 8 min ; prévoir 1 min de marge (visée 7 min)
- [ ] Avoir le `ci.yml` ouvert sur le dernier commit pour les questions techniques
- [ ] Questions probables du jury — réponses prêtes :
  - *« Pourquoi GitHub Actions plutôt que Jenkins ? »* → intégration native, pas d'infra à gérer, marketplace, workflow-as-code ; Jenkins plus flexible/personnalisable mais à auto-héberger
  - *« Comment déclencher un workflow sur un horaire ? »* → clause `on: schedule` avec cron
  - *« Comment les jobs s'enchaînent-ils ? »* → `needs` (le job suivant attend les précédents) + `if` (conditions, ex. branche main)
  - *« Où tournent les jobs ? »* → sur les runners hébergés (ubuntu-latest) ; possibles self-hosted runners
  - *« Comment Trivy bloque-t-il le pipeline ? »* → `exit-code: 1` si vulnérabilité HIGH/CRITICAL → job rouge → les jobs en `needs` ne démarrent pas
