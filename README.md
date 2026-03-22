# Saulzet & Vous

Plateforme de signalement citoyen pour la commune de **Saulzet-le-Froid** (Puy-de-Dôme).

Les habitants signalent des problèmes (voirie, eau, éclairage…) et les élus prennent en charge leur résolution.

## Stack technique

- **Backend** : Django 5.x (Python 3.12+)
- **Frontend** : HTMX + Alpine.js + Tailwind CSS + DaisyUI
- **BDD** : SQLite (dev) / PostgreSQL (prod)

## Installation

```bash
# Cloner le projet
git clone https://github.com/saulzet-le-froid/saulzet-et-vous.git
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

## Licence

Logiciel libre sous [licence MIT](LICENCE).
