# CLAUDE.md — Saulzet & Vous

## Projet

Site communal et plateforme de démocratie participative pour Saulzet-le-Froid (287 hab., Puy-de-Dôme).
Le site comprend un CMS intégré (pages éditables, documents) et un module participatif « Saulzet & Vous » où les habitants écrivent à leurs élus (questions, idées, signalements).
Logiciel libre MIT — repo `ojautzy/saulzet-et-vous`.

## Stack

- **Backend** : Django 5.2, Python 3.12+
- **Frontend** : HTMX 2.x + Alpine.js 3.x + Tailwind CSS 3.x + DaisyUI 4.x (thème custom "saulzet")
- **CMS** : django-tinymce 5.x (éditeur WYSIWYG pour les pages), app `pages`
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

# Migration de contenu (Phase 5)
python manage.py build_inventory           # Inventaire du site aspiré
python manage.py migrate_content           # Dry run migration
python manage.py migrate_content --execute # Migration effective
python manage.py create_initial_pages      # Arborescence initiale des pages
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

- `admin` : gestion technique, validation inscriptions, nettoyage (suppression sollicitations annulées/résolues)
- `secretary` : secrétaire de mairie — édition des pages CMS et documents via l'admin Django (accès `is_staff`, permissions limitées à `pages.*`)
- `mayor` : supervision, affectation/réaffectation des sollicitations, dashboard de pilotage
- `elected` : prise en charge, commentaires, clôture, bascule public/privé
- `citizen` : création, suivi, modification de ses sollicitations, choix public/privé (tant que statut NEW)

## Règles métier clés

- **Visibilité** : une sollicitation peut être publique ou privée (`is_public`). L'habitant peut changer la visibilité tant que le statut est NEW. Après prise en charge, seul l'élu peut basculer la visibilité.
- **Modification** : l'habitant peut modifier localisation, photos et visibilité tant que la sollicitation n'est pas résolue ou annulée. Le titre et la description ne sont pas modifiables.
- **Tableau de bord public** : affiche les sollicitations publiques avec statut ASSIGNED ou IN_PROGRESS, visible par tous les utilisateurs connectés.
- **Pages CMS** : les pages publiées sont accessibles à tous (visiteurs non connectés). L'édition est réservée aux rôles `secretary`, `mayor` et `admin` via l'admin Django.
- **Module participatif** : sous le préfixe `/etvous/`, requiert une connexion et un compte approuvé.

## Structure des URLs

- `/` : page d'accueil portail communal (publique)
- `/comptes/` : authentification (login, inscription, magic link)
- `/etvous/` : module participatif (sollicitations)
- `/etvous/tableau-de-bord/` : dashboard élus et maire
- `/contact/`, `/documents/` : pages CMS spéciales
- `/gestion/migration/` : interface de validation migration (admin/maire)
- `/<slug>/`, `/<parent>/<slug>/` : pages CMS catch-all

### Arborescence des pages CMS

- `/mairie/` — La mairie (équipe, horaires, conseil, commissions)
- `/commune/` — La commune (présentation, villages, accès, associations)
- `/demarches/` — Démarches administratives (état civil, identité, urbanisme, en ligne)
- `/vie-quotidienne/` — Vie quotidienne (services, jeunesse, déchets, eau)
- `/decouvrir/` — Découvrir Saulzet (patrimoine, saint-nectaire, galerie)
- `/documents/` — Documents officiels (PV, bulletins, PLU, arrêtés)
- `/contact/` — Contact

## Accès dev

- URL tunnel Cloudflare : https://saulzet.jautzy.com
- Domaine de production : saulzet-le-froid.com
- Coordonnées Saulzet-le-Froid (Le Bourg) : lat 45.6415, lng 2.9178

## Versioning

- La version du projet est définie dans le fichier `VERSION` à la racine (ex: `0.3.0`)
- Elle est affichée dans le footer du site via le context processor `saulzet_et_vous.context_processors.version`
- **Règle impérative** : à chaque création de tag Git (`git tag vX.Y.Z`), mettre à jour le fichier `VERSION` avec la même valeur (sans le préfixe `v`). Toujours committer la mise à jour de `VERSION` **avant** de créer le tag.
- Schéma : `MAJEURE.MINEURE.PATCH` — une phase de développement = une version mineure

## Médias et documents

- **Documents** (PDF, etc.) : stockés dans `media/documents/`, gérés via le modèle `Document` de l'app `pages`. Référencer dans les pages CMS avec `<a href="/media/documents/nom.pdf">`.
- **Images des pages** : stockées dans `media/pages/images/`. Référencer dans les pages CMS avec `<img src="/media/pages/images/nom.jpg">`.
- **Templates spéciaux** : certaines pages utilisent des templates dédiés (`habitants` pour la courbe démographique Chart.js, `acces` pour la carte Leaflet, `equipe`, `contact`, `documents`).

## État du projet

- **Version actuelle** : 0.7.0 (Phase 5 — Migration du contenu existant)
- Plan complet dans `saulzet-et-vous-plan-v3.md`. Prompts par phase dans `prompt-phase*-claude-code.md`.
- Phases 1 à 5 implémentées. Migration du contenu de l'ancien site e-monsite effectuée (99 documents, 44 images, 30+ pages CMS). Prochaine étape : Phase 6.
