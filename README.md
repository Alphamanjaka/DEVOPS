# Démonstration Technique : Pipeline DevOps & Application de Messagerie

Ce projet est une démonstration technique d'une chaîne **DevOps complète** appliquée à une application web Django. L'objectif est de montrer l'automatisation des tests, la conteneurisation et le déploiement continu, ainsi que des fonctionnalités applicatives spécifiques.

## Architecture & Technologies

- **Backend :** Django (Python) avec Gunicorn.
- **Base de données :** PostgreSQL 15.
- **Conteneurisation :** Docker & Docker Compose.
- **CI/CD :** GitHub Actions.
- **Frontend :** HTML5, CSS3 (Responsive), FontAwesome.

---

## 🚀 Pipeline CI/CD (GitHub Actions)

Le workflow est défini dans `.github/workflows/ci.yml` et se divise en deux étapes majeures :

```mermaid
flowchart LR
    %% Déclencheur
    Trigger([Push sur branche 'main']) --> CI

    %% Job 1 : Intégration Continue
    subgraph CI [Job: Intégration Continue]
        direction TB
        Step1[Checkout Code] --> Step2[Création .env Test]
        Step2 --> Step3[Tests Unitaires<br/>(Docker Compose)]
    end

    %% Condition de transition
    CI -- Si Succès --> CD
    CI -- Si Échec --> Fail([Arrêt du Pipeline])

    %% Job 2 : Livraison Continue
    subgraph CD [Job: Livraison Continue]
        direction TB
        Step4[Checkout Code] --> Step5[Login GHCR]
        Step5 --> Step6[Build Image Prod]
        Step6 --> Step7[Push Image vers Registry]
    end

    %% Résultat final
    CD --> Success([Image prête à déployer<br/>sur GHCR])

    %% Styles pour la lisibilité
    classDef success fill:#e6fffa,stroke:#2c7a7b,stroke-width:2px;
    classDef failure fill:#fff5f5,stroke:#c53030,stroke-width:2px;
    classDef process fill:#ebf8ff,stroke:#2b6cb0,stroke-width:2px;

    class Trigger,Success success
    class Fail failure
    class Step1,Step2,Step3,Step4,Step5,Step6,Step7 process
```

### 1. Intégration Continue (CI)

À chaque `push` sur la branche `main` :

- **Environnement de Test :** Création dynamique d'un fichier `.env` sécurisé pour l'environnement de test.
- **Dockerisation des Tests :** Utilisation de `docker compose run` pour monter les services (Postgres + Django).
- **Exécution :** Lancement automatique des tests unitaires (`python manage.py test`).

### 2. Livraison Continue (CD)

_Condition :_ Ne s'exécute que si la CI réussit.

- **Authentification :** Connexion sécurisée au **GitHub Container Registry (GHCR)**.
- **Build & Push :** Construction de l'image Docker de production et publication sur le registre (`ghcr.io/...`).

---

## 🐳 Configuration Docker

L'application est entièrement conteneurisée pour garantir la cohérence entre le développement et la production.

- **Orchestration :** Le fichier `docker-compose.yml` gère les services `db` (Postgres) et `web` (Django).
- **Script de Démarrage (`build.sh`) :**
  - Application automatique des migrations (`migrate`).
  - Collecte des fichiers statiques (`collectstatic`).
  - Création conditionnelle d'un superutilisateur.
  - Lancement du serveur de production **Gunicorn**.
- **Hot Reload (Dev) :** Utilisation de `develop.watch` dans Docker Compose pour synchroniser les changements de code en temps réel sans reconstruire l'image.

---

## ✨ Fonctionnalités de l'Application

### Importation de Messages (CSV)

L'application dispose d'un module d'importation de données en masse.

- **Format supporté :** `Contenu du message, AAAA-MM-JJ HH:MM:SS, Username`
- **Interface :** Formulaire dédié avec gestion des erreurs et messages flash (Succès/Avertissement/Erreur).

### Interface Utilisateur (UI/UX)

- **Design Responsive :** Sidebar adaptative (mobile/desktop) gérée via CSS (`style.css`).
- **Thème :** Utilisation de variables CSS pour une maintenance facile des couleurs.

---

## 📸 Captures d'écran

<!--
INSTRUCTIONS POUR AJOUTER VOS IMAGES :
1. Créez un dossier nommé "screenshots" à la racine du projet.
2. Mettez vos images dedans (ex: pipeline.png, import.png).
3. Décommentez les lignes ci-dessous.
-->

### Pipeline GitHub Actions

<!-- !Pipeline CI/CD -->

_Vue du workflow réussissant les étapes de test et de déploiement._

### Interface d'Import CSV

<!-- !Import CSV -->

_Formulaire d'importation avec feedback utilisateur._

---

## Comment lancer le projet en local

1. **Cloner le dépôt :**
   ```bash
   git clone <votre-url-repo>
   ```
2. **Lancer avec Docker Compose :**
   ```bash
   docker compose up --build
   ```
