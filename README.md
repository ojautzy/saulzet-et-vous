# Saulzet & Vous

Plateforme de démocratie participative pour la commune de **Saulzet-le-Froid** (284 hab., Puy-de-Dôme).

Les habitants écrivent à leurs élus (questions, idées, signalements) via un formulaire web. Les élus disposent d'un tableau de bord pour prendre en charge, suivre et répondre aux sollicitations.

## Stack technique

- **Backend** : Django 5.2 (Python 3.12+)
- **Frontend** : HTMX 2.x + Alpine.js 3.x + Tailwind CSS 3.x + DaisyUI 4.x
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

Le tunnel est déjà configuré côté Cloudflare. Il suffit de lancer le serveur Django sur `0.0.0.0:8000` pour que l'application soit accessible.

## Rôles utilisateur

| Rôle | Description |
|------|-------------|
| `admin` | Administrateur technique |
| `mayor` | Maire et 1er Adjoint |
| `elected` | Adjoint ou Conseiller municipal |
| `citizen` | Habitant |

## Fonctionnalités

- **Authentification** : inscription avec validation admin, connexion par magic link ou mot de passe
- **Sollicitations** : les habitants créent des questions, idées ou signalements avec photos et géolocalisation
- **Tableau de bord élus** : vue d'ensemble avec filtres, compteurs par statut, page « Mes tâches »
- **Workflow** : prise en charge, affectation (maire), suivi, clôture avec réponse
- **Commentaires** : timeline chronologique des échanges et changements de statut

## Versioning

La version du projet est dans le fichier `VERSION` à la racine et affichée dans le footer du site.
Elle suit le schéma `MAJEURE.MINEURE.PATCH` et doit toujours être synchronisée avec le tag Git.

## Licence

Logiciel libre sous [licence MIT](LICENCE).
