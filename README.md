# Saulzet & Vous

Site communal et plateforme de démocratie participative pour la commune de **Saulzet-le-Froid** (284 hab., Puy-de-Dôme).

Le site comprend :
- Un **site communal** avec pages éditables (CMS intégré), documents officiels, page de contact et équipe municipale
- Une **plateforme participative** « Saulzet & Vous » où les habitants écrivent à leurs élus (questions, idées, signalements)

## Stack technique

- **Backend** : Django 5.2 (Python 3.12+)
- **Frontend** : HTMX 2.x + Alpine.js 3.x + Tailwind CSS 3.x + DaisyUI 4.x
- **CMS** : django-tinymce 5.x (éditeur WYSIWYG)
- **Cartographie** : Leaflet.js + OpenStreetMap
- **BDD** : SQLite (dev) / PostgreSQL (prod)

## Installation

```bash
# Cloner le projet
git clone https://github.com/ojautzy/saulzet-et-vous.git
cd saulzet-et-vous

# Environnement Python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt        # production
pip install -r requirements-dev.txt    # développement (inclut pytest, ruff)

# Dépendances frontend
npm install

# Compiler le CSS
npm run build:css

# Variables d'environnement
cp .env.example .env
# Éditez .env selon vos besoins

# Base de données
python manage.py migrate

# Créer un super-administrateur
python manage.py createsuperadmin

# Lancer le serveur
python manage.py runserver 0.0.0.0:8000
```

## Développement

Pour recompiler automatiquement le CSS Tailwind à chaque modification :

```bash
npm run watch:css
```

### Linting et formatage

```bash
ruff check .
ruff format .
```

### Tests

```bash
pytest
```

## Accès distant (tunnel Cloudflare)

L'application est exposée sur Internet via un tunnel Cloudflare à l'adresse :

**https://saulzet.jautzy.com**

Domaine de production : **saulzet-le-froid.com**

## Rôles utilisateur

| Rôle | Description |
|------|-------------|
| `admin` | Administrateur technique |
| `secretary` | Secrétaire de mairie — édition des pages et documents |
| `mayor` | Maire et 1er Adjoint — pilotage, affectation |
| `elected` | Adjoint ou Conseiller municipal |
| `citizen` | Habitant |

## Fonctionnalités

### Site communal
- **Pages CMS** : pages éditables avec TinyMCE, menu dynamique, fil d'Ariane
- **Documents** : PV de conseil, bulletins, arrêtés, documents PLU
- **Équipe municipale** : page avec photos et fonctions des élus
- **Contact** : formulaire de contact avec envoi par email
- **Page d'accueil** : portail communal avec accès rapides et actualités

### Module participatif (Saulzet & Vous)
- **Authentification** : inscription avec validation admin, connexion par magic link ou mot de passe
- **Sollicitations** : les habitants créent des questions, idées ou signalements avec photos et géolocalisation
- **Tableau de bord élus** : vue d'ensemble avec filtres, compteurs par statut, page « Mes tâches »
- **Dashboard Maire** : indicateurs globaux, charge par élu, sollicitations orphelines, statistiques
- **Workflow** : prise en charge, affectation (maire), suivi, clôture avec réponse
- **Commentaires** : timeline chronologique des échanges et changements de statut

## Versioning

La version du projet est dans le fichier `VERSION` à la racine et affichée dans le footer du site.
Elle suit le schéma `MAJEURE.MINEURE.PATCH` et doit toujours être synchronisée avec le tag Git.

## Licence

Logiciel libre sous [licence MIT](LICENCE).
