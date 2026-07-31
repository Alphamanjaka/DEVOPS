# Présentation 8 min — GitHub Actions comme outil DevOps

**Format :** Slides uniquement (sans démo live) — screenshots intégrés dans les slides.
**Sujet :** **GitHub Actions** en tant qu'outil DevOps, en 3 parties.
**Cas d'usage :** le projet *Messagerie* (Django) pour la partie mise en place.
**Déployé :** https://devops-omjy.onrender.com

---

## Plan d'ensemble (8 min)

| # | Slide | Timing | Durée |
|---|---|---|---|
| 1.1 | Qu'est-ce que GitHub Actions + 4 points essentiels + pourquoi | 0:00 – 1:20 | 1min20 |
| 1.2 | Principe de fonctionnement & architecture | 1:20 – 2:30 | 1min10 |
| 1.3 | Composants principaux | 2:30 – 3:30 | 1min00 |
| 2.1 | Mise en place — Objectif & pré-requis | 3:30 – 4:30 | 1min00 |
| 2.2 | Mise en place — Étapes | 4:30 – 6:00 | 1min30 |
| 3.1 | Les forces de GitHub Actions (4 points) | 6:00 – 7:00 | 1min00 |
| 3.2 | Les limites (3 points) + conclusion | 7:00 – 8:00 | 1min00 |

---

# PARTIE 1 — PRÉSENTATION DE GITHUB ACTIONS

## Slide 1.1 — Qu'est-ce que GitHub Actions ? (0:00 → 1:20)

**Contenu de la slide :**
- Définition : *un service d'intégration et de déploiement continus (CI/CD) intégré à GitHub, qui exécute automatiquement des tâches définies dans le dépôt, à chaque événement Git.*
- **4 points essentiels** (ce que c'est) :
  1. **CI/CD intégré à GitHub** — pas d'outil externe, pas de serveur à installer
  2. **Configuré par du code** — des fichiers YAML dans `.github/workflows/`
  3. **Exécution sur des runners** — machines gérées par GitHub (ou auto-hébergées)
  4. **Un écosystème d'actions** réutilisables depuis un Marketplace
- **Pourquoi GitHub Actions** :
  - Déjà présent dans le dépôt : zéro infrastructure à administrer
  - Workflow-as-code : la config est versionnée, revue et historisée avec le code
  - Gratuit pour les dépôts publics, résultats visibles dans l'onglet Actions
- Screenshot : onglet Actions du repo

**Texte à dire (≈1min20) :**
> « Première partie : présentation de l'outil.
> **GitHub Actions, c'est quoi ?** C'est un service d'intégration et de déploiement continus, intégré directement à GitHub. Il déclenche automatiquement des tâches — tester, construire, déployer — à chaque événement du dépôt, comme un push ou une pull request.
> Quatre points le définissent. D'abord, la CI/CD est **intégrée à GitHub** : aucun serveur Jenkins à installer ni à maintenir. Ensuite, tout est **configuré par du code** : des fichiers YAML rangés dans `.github/workflows/`. Troisièmement, l'exécution se fait sur des **runners** — des machines fournies par GitHub. Et enfin, il s'appuie sur un **écosystème d'actions** réutilisables, comparables à des modules.
> Pourquoi le choisir ? Parce qu'il est **déjà dans le dépôt**, que la configuration est versionnée comme le code, et que le résultat s'affiche dans l'onglet Actions. »

**Transition :** « Voyons maintenant comment l'outil fonctionne. »

---

## Slide 1.2 — Principe de fonctionnement & architecture (1:20 → 2:30)

**Contenu de la slide :** schéma d'architecture
```
Événement Git ──▶ GitHub (plateforme) ──▶ Runners (VM ubuntu-latest)
  push / PR        - détecte le workflow   - exécutent les jobs
                   - lit le YAML           - chaque job = steps
                   - orchestre les runners
                                                ▼
                    Statut + logs + artifacts (visibles dans l'onglet Actions)
```
- Principe : *un événement Git déclenche un workflow ; le workflow s'exécute en jobs sur des runners ; chaque job enchaîne des steps ; tout est tracé dans GitHub.*
- Exemple réel (projet Messagerie) : push → 4 jobs (tests, lint, security, build-and-push)
- Screenshot : run avec jobs en parallèle puis enchaînement

**Texte à dire (≈1min10) :**
> « Le principe de fonctionnement est simple : **un événement Git déclenche un workflow**.
> Quand un push ou une pull request arrive, la plateforme GitHub détecte le workflow correspondant — c'est-à-dire qu'elle lit le fichier YAML — puis répartit les jobs sur des **runners**, des machines virtuelles Linux, Windows ou macOS. Chaque job enchaîne ses étapes, et tout — logs, statut, fichiers produits — est tracé et visible dans l'onglet Actions.
> L'architecture tient donc en trois acteurs : la **plateforme GitHub** qui orchestre, les **runners** qui exécutent, et le **workflow YAML** qui décrit quoi faire.
> Sur notre projet, un push sur la branche principale déclenche quatre jobs, dont certains en parallèle. Le parallélisme est d'ailleurs un des atouts du principe : les contrôles indépendants ne se font pas attendre les uns les autres. »

**Transition :** « Détaillons les composants. »

---

## Slide 1.3 — Composants principaux (2:30 → 3:30)

**Contenu de la slide :** 7 composants avec un mot clé chacun
| Composant | Rôle | Exemple réel |
|---|---|---|
| **Workflow** | Fichier YAML décrivant l'automatisation | `.github/workflows/ci.yml` |
| **Déclencheur (`on`)** | Événement qui démarre le workflow | `push` sur main/develop, `pull_request` |
| **Job** | Ensemble d'étapes sur un runner | `tests`, `lint`, `security` |
| **Step** | Une commande ou une action | `coverage run manage.py test` |
| **Action** | Brique réutilisable (Marketplace) | `actions/checkout@v4`, `trivy-action` |
| **Runner** | Machine d'exécution | `ubuntu-latest` |
| **Env / Secrets / Artifacts** | Configuration et résultats | `GITHUB_TOKEN`, `coverage.xml`, SARIF |

**Texte à dire (≈1min) :**
> « Sept composants suffisent pour tout comprendre.
> Le **workflow**, d'abord : le fichier YAML qui décrit toute l'automatisation. Son **déclencheur**, la clause `on`, qui définit quels événements le lancent. Un workflow contient des **jobs**, exécutés sur des **runners** — chacun définit les **steps** à enchaîner. Une step est soit une commande directe, soit une **action**, une brique réutilisable du Marketplace.
> Enfin, l'outil gère l'**environnement** : les **secrets** comme le token GitHub, les variables d'**environnement**, et les **artifacts** — des fichiers de sortie téléchargeables, comme le rapport de couverture ou le rapport de sécurité SARIF.
> Avec ces sept briques, on peut construire n'importe quel pipeline. »

**Transition :** « Passons à la mise en place concrète dans un projet. »

---

# PARTIE 2 — MISE EN PLACE DANS UN PROJET

## Slide 2.1 — Objectif & pré-requis (3:30 → 4:30)

**Contenu de la slide :**
- **Objectif** : automatiser à chaque commit la chaîne complète — tests → qualité → sécurité → build → publication → déploiement — sans intervention manuelle
- **Pré-requis** :
  1. Un **dépôt GitHub** (avec son code source)
  2. Le **code à tester** (ici Django + Docker) — workflow écrit après le Dockerfile/docker-compose
  3. Un **registre** pour l'image (GHCR) — l'authentification via `GITHUB_TOKEN` (fourni automatiquement)
  4. **Aucun serveur** — les runners sont hébergés
- Screenshot : structure du repo (`.github/workflows/ci.yml`)

**Texte à dire (≈1min) :**
> « Deuxième partie : la mise en place dans un projet, avec le projet Messagerie comme exemple.
> **L'objectif** : qu'à chaque commit, toute la chaîne s'exécute automatiquement — les tests, la qualité, la sécurité, puis la construction de l'image, sa publication et le déploiement — sans aucune intervention manuelle.
> Les **pré-requis** sont légers. Il faut un dépôt GitHub avec le code source. Il faut que le projet soit **testable** — ici, un Dockerfile et un docker-compose, qui seront réutilisés dans les jobs. Il faut éventuellement un registre d'images ; GitHub fournit le sien, le GHCR, avec un token d'authentification généré automatiquement.
> Et c'est tout : pas de serveur à provisionner, les runners sont fournis par GitHub. »

**Transition :** « Concrètement, comment ça se met en place ? »

---

## Slide 2.2 — Étapes de mise en place (4:30 → 6:00)

**Contenu de la slide :** 7 étapes numérotées
1. **Créer le dossier** `.github/workflows/` à la racine du dépôt
2. **Écrire le workflow** YAML : nom, déclencheurs `on`, puis les jobs
3. **Définir chaque job** : runner, steps (actions ou commandes), dépendances `needs`, conditions `if`
4. **Ajouter les secrets** (Settings → Secrets) — `GITHUB_TOKEN` est automatique
5. **Pousser le code** → le workflow se lance, vérifier l'onglet Actions
6. **Protéger les branches** : statuts requis pour le merge des PR
7. **Itérer** : artifacts, scans de sécurité, Dependabot
- Exemple : le job `tests` du projet (screenshot YAML) : .env → compose build → migrations → coverage ≥70% → seed data → health check → artifact

**Texte à dire (≈1min30) :**
> « La mise en place se fait en sept étapes.
> On crée d'abord le dossier `.github/workflows/` à la racine. On **écrit le workflow** : un nom, les déclencheurs — ici push sur main et develop, pull request vers main — puis les jobs. Chaque job déclare son runner, ses steps, et ses relations : `needs` pour dépendre d'un autre job, `if` pour des conditions.
> Les **secrets** se configurent dans les paramètres du dépôt ; le plus important, le `GITHUB_TOKEN`, est fourni automatiquement par GitHub à chaque exécution.
> On **pousse le code**, et le workflow se lance immédiatement — c'est l'onglet Actions qui montre le résultat.
> Pour un projet d'équipe, on **protège la branche principale** : un job en échec bloque la fusion d'une pull request.
> Et on **itère** : ici, le job de tests reproduit l'environnement complet — il construit l'image, démarre PostgreSQL, applique les migrations, mesure la couverture avec un seuil bloquant, rejoue le jeu de données et fait un health check, puis publie le rapport de couverture en artifact.
> En quelques commits, un pipeline complet est en place. »

**Transition :** « Dernière partie : les forces et les limites de l'outil. »

---

# PARTIE 3 — FORCES ET LIMITES

## Slide 3.1 — Les forces de GitHub Actions (4 points) (6:00 → 7:00)

**Contenu de la slide :** 4 points forts
1. **Intégration native à GitHub** — PR checks, onglet Security, secrets : tout est articulé (le scan Trivy alimente le Security tab via SARIF)
2. **Écosystème Marketplace** — actions prêtes à l'emploi (checkout, setup-python, Trivy, CodeQL, pre-commit) → on ne réécrit rien
3. **Workflow-as-code** — la config est du code : versionnée, revue en PR, historisée avec le dépôt
4. **Zéro infrastructure** — runners hébergés, gratuit sur les dépôts publics, parallélisme des jobs

**Texte à dire (≈1min) :**
> « Dernière partie : qu'est-ce qui fait la force de GitHub Actions ? Quatre points.
> Premièrement, **l'intégration native à GitHub** : le pipeline dialogue directement avec les pull requests, les secrets et l'onglet Security — par exemple, le scan Trivy importe son rapport SARIF directement dans le Security tab du dépôt.
> Deuxièmement, **l'écosystème Marketplace** : des briques réutilisables, `checkout`, `setup-python`, `trivy-action`, `pre-commit` — on assemble plutôt qu'on réécrit.
> Troisièmement, **le workflow-as-code** : la configuration est du code comme les autres — revue en pull request, versionnée, historisée.
> Et quatrièmement, **zéro infrastructure** : pas de serveur à héberger, gratuit pour les dépôts publics, et des jobs qui s'exécutent en parallèle pour gagner du temps. »

**Transition :** « Restons honnêtes : l'outil a aussi des limites. »

---

## Slide 3.2 — Les limites (3 points) + conclusion (7:00 → 8:00)

**Contenu de la slide :** 3 limites
1. **Dépendance à l'écosystème GitHub** (vendor lock-in) — changer de plateforme impose de réécrire les workflows
2. **Coût et performances sur les dépôts privés** — quota limité gratuit ; runners partagés → performances variables
3. **Courbe d'apprentissage** — YAML verbeux sur les gros pipelines, débogage des expressions et des conditions

- **Conclusion** : un outil CI/CD complet, intégré, configurable par code — le meilleur rapport simplicité/puissance pour un dépôt hébergé sur GitHub ; les limites restent mineures pour ce type de projet.
- « Merci — questions ? »

**Texte à dire (≈1min) :**
> « Trois limites à connaître.
> D'abord, la **dépendance à l'écosystème GitHub** : la configuration est spécifique à la plateforme, et la quitter imposerait de tout réécrire. Ensuite, sur un **dépôt privé**, la gratuité est limitée et les runners étant partagés, les performances peuvent varier. Enfin, il y a une **courbe d'apprentissage** : les expressions, les conditions et la syntaxe YAML peuvent devenir verbeuses sur les gros pipelines.
> Pour conclure : GitHub Actions est un outil de CI/CD complet et intégré, où tout se configure par du code. Pour un projet hébergé sur GitHub, c'est probablement le meilleur compromis entre simplicité et puissance — et ses limites restent mineures au regard de ce qu'il automatise.
> Merci, je vous écoute. »

---

## Check-list avant la présentation

- [ ] Vérifier que https://devops-omjy.onrender.com/health/ répond `"status": "ok"`
- [ ] Screenshots à jour :
  - Onglet **Actions** : liste des runs + exécution avec les 4 jobs (tests, lint, security, build-and-push)
  - **YAML** du workflow annoté (`ci.yml`) — étapes, `needs`, `if`, secrets
  - Structure du dépôt montrant `.github/workflows/ci.yml`
  - **Logs** d'une step (ex. tests + coverage)
  - **Artifact** `coverage-report` + rapport **SARIF** dans Security tab
  - **Secrets** et **Dependabot**, **branch protection** (status checks requis)
- [ ] Répéter le timing : Partie 1 ≈ 3min30, Partie 2 ≈ 2min30, Partie 3 ≈ 2min
- [ ] Avoir le `ci.yml` ouvert sur le dernier commit pour les questions techniques
- [ ] Questions probables du jury — réponses prêtes :
  - *« Pourquoi GitHub Actions plutôt que Jenkins ? »* → intégration native, pas d'infra à héberger, marketplace, workflow-as-code ; Jenkins plus flexible/personnalisable mais à auto-héberger
  - *« Comment déclencher un workflow sur un horaire ? »* → clause `on: schedule` avec une expression cron
  - *« Comment les jobs s'enchaînent-ils ? »* → `needs` (dépendances) + `if` (conditions, ex. branche main)
  - *« Où tournent les jobs ? »* → runners hébergés (ubuntu-latest) ; possibles runners self-hosted pour le privé
  - *« Comment Trivy bloque-t-il le pipeline ? »* → `exit-code: 1` si vulnérabilité HIGH/CRITICAL → job rouge → les jobs en `needs` ne démarrent pas
