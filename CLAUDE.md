# CLAUDE.md — Saulzet & Vous

## Projet

Plateforme de démocratie participative pour Saulzet-le-Froid (284 hab., Puy-de-Dôme).
Les habitants écrivent à leurs élus (questions, idées, signalements) via un formulaire web.
Logiciel libre MIT — repo `ojautzy/saulzet-et-vous`.

## Stack

- **Backend** : Django 5.2, Python 3.12+
- **Frontend** : HTMX 2.x + Alpine.js 3.x + Tailwind CSS 3.x + DaisyUI 4.x (thème custom "saulzet")
- **Cartographie** : Leaflet.js + OpenStreetMap
- **BDD dev** : SQLite
- **Tests** : pytest + pytest-django
- **Linting** : ruff

## Commandes

```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000   # Serveur dev
npm run build:css                          # Compiler Tailwind
npm run watch:css                          # Tailwind en mode watch
ruff check .                               # Linting
pytest                                     # Tests
python manage.py makemigrations && python manage.py migrate
```

## Conventions

- **Langue du code** : anglais (modèles, variables, fonctions)
- **Langue de l'interface** : français — utiliser `{% trans %}` dans les templates, avec accents
- **Langue de la documentation** : français
- Les textes dans `{% trans %}` et `_()` doivent inclure les accents (pas de fichiers .po)
- Templates dans `templates/` (pas dans les apps)
- Composants réutilisables dans `templates/components/`
- Settings séparés : `saulzet_et_vous/settings/{base,dev,prod}.py`
- Utiliser `settings.AUTH_USER_MODEL` pour les ForeignKey vers User

## Charte visuelle

- **Polices** : Playfair Display (titres), Source Sans 3 (interface), Source Serif 4 (contenu rédigé)
- **Couleurs** : vert-foret #2D5016, vert-prairie #4A7C28, terre-claire #C49A2A, crème #FDF8F0
- **Composants** : `btn-primary-saulzet`, `btn-secondary-saulzet`, `card-saulzet` (définis dans input.css)
- Mobile-first, WCAG AA

## Architecture des rôles

- `admin` : gestion technique, validation inscriptions
- `mayor` : supervision, affectation des sollicitations
- `elected` : prise en charge, commentaires, clôture
- `citizen` : création et suivi de ses sollicitations

## Accès dev

- URL tunnel Cloudflare : https://saulzet.jautzy.com
- Coordonnées Saulzet-le-Froid : lat 45.6565, lng 2.9162

## Versioning

- La version du projet est définie dans le fichier `VERSION` à la racine (ex: `0.3.0`)
- Elle est affichée dans le footer du site via le context processor `saulzet_et_vous.context_processors.version`
- **Règle impérative** : à chaque création de tag Git (`git tag vX.Y.Z`), mettre à jour le fichier `VERSION` avec la même valeur (sans le préfixe `v`). Toujours committer la mise à jour de `VERSION` **avant** de créer le tag.
- Schéma : `MAJEURE.MINEURE.PATCH` — une phase de développement = une version mineure

## État du projet

Plan complet dans `saulzet-et-vous-plan-v2.md`. Prompts par phase dans `prompt-phase*-claude-code.md`.
