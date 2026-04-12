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

# Notifications
python manage.py send_reminders            # Relances sollicitations orphelines
python manage.py send_reminders --dry-run  # Prévisualisation sans envoi
python manage.py send_reminders --days 3   # Seuil personnalisé

# Migration de contenu (Phase 5 — référence)
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
- **Zéro valeur en dur** : ne jamais coder en dur dans les templates ou le code Python des valeurs susceptibles de changer (coordonnées mairie, téléphone, horaires, email, seuils métier, coordonnées GPS…). Toutes ces valeurs doivent être stockées dans le modèle `SiteSettings` (singleton, app `settings_app`) et accessibles via `SiteSettings.load()` dans le code Python ou `{{ site_settings.* }}` dans les templates. Ce principe garantit que le site reste administrable par un non-technicien (secrétaire, maire) sans intervention développeur, et qu'il survit aux changements d'équipe municipale.

## Charte visuelle

- **Polices** : Playfair Display (titres), Source Sans 3 (interface), Source Serif 4 (contenu rédigé)
- **Couleurs** : vert-foret #2D5016, vert-prairie #4A7C28, terre-claire #C49A2A, crème #FDF8F0
- **Composants** : `btn-primary-saulzet`, `btn-secondary-saulzet`, `card-saulzet` (définis dans input.css)
- Mobile-first, WCAG AA

## Architecture des rôles

- `admin` : gestion technique, validation inscriptions, nettoyage (suppression sollicitations annulées/résolues)
- `secretary` : secrétaire de mairie — édition des pages CMS, documents et catégories de documents via l'admin Django (accès `is_staff`, permissions limitées à `pages.*`). Lien « Édition » dans le menu Saulzet & Vous.
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
- `/etvous/tableau-de-bord/inscriptions/` : validation des inscriptions (maire/admin)
- `/etvous/tableau-de-bord/export/` : export CSV des sollicitations (maire/admin)
- `/etvous/tableau-de-bord/journal/` : journal d'audit (admin)
- `/etvous/notifications/` : centre de notifications
- `/etvous/notifications/preferences/` : préférences email
- `/contact/`, `/documents/` : pages CMS spéciales
- `/mentions-legales/` : page de mentions légales (liée depuis le footer)
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

## Sanitisation HTML CMS (nh3)

Le contenu HTML des pages CMS est sanitisé à la sauvegarde via `nh3` (cf. `apps/pages/models.py`). La liste blanche de balises et attributs autorisés est définie dans les constantes `ALLOWED_TAGS` et `ALLOWED_ATTRIBUTES` en haut du fichier. Elle couvre les usages TinyMCE actuels : titres, paragraphes, listes, tableaux, images, liens, mise en forme inline. **Si un nouveau type de contenu est ajouté** (embed vidéo, iframe, etc.), mettre à jour ces constantes.

## Protection anti-spam du formulaire de contact

Le formulaire `/contact/` est protégé par 3 couches anti-bot (cf. `apps/pages/forms.py` et `apps/pages/views.py`) :
1. **Honeypot** : champ `website` invisible (CSS `position:absolute;left:-9999px`), rejeté silencieusement si rempli.
2. **Rate limiting** : `@ratelimit(key="ip", rate="3/m")` via `django-ratelimit` — max 3 soumissions/minute par IP.
3. **Validation temporelle** : timestamp caché injecté au GET, rejeté si soumission en moins de 3 secondes (`CONTACT_MIN_SUBMIT_SECONDS`).

Les tests anti-spam désactivent le rate limiter via `settings.RATELIMIT_ENABLE = False` (fixture `_disable_ratelimit`). Le test du rate limiting lui-même est dans `TestContactRateLimit` (rate limiter activé).

## Médias et documents

- **Documents** (PDF, etc.) : stockés dans `media/documents/`, gérés via le modèle `Document` de l'app `pages`. Les catégories de documents sont dynamiques (modèle `DocumentCategory`), administrables par la secrétaire et l'admin via l'interface Django. Référencer dans les pages CMS avec `<a href="/media/documents/nom.pdf">`.
- **Images des pages** : stockées dans `media/pages/images/`. Référencer dans les pages CMS avec `<img src="/media/pages/images/nom.jpg">`.
- **Templates spéciaux** : certaines pages utilisent des templates dédiés (`habitants` pour la courbe démographique Chart.js, `acces` pour la carte Leaflet, `galerie` pour la visionneuse lightbox, `equipe`, `contact`, `documents`).

## SiteSettings (singleton)

Le modèle `SiteSettings` (app `settings_app`) centralise tous les paramètres éditables du site :
- **Identité** : nom du site, commune, population
- **Coordonnées** : adresse, téléphone, horaires
- **Email** : expéditeur, contact, configuration SMTP
- **Cartographie** : centre carte, coordonnées mairie, zoom
- **Seuils métier** : orphan_days, cleanup_days, stats_period_days, reminder_interval_days

Accès : `SiteSettings.load()` en Python, `{{ site_settings.* }}` dans les templates (context processor).
Le backend email (`DatabaseEmailBackend`) lit la config SMTP depuis SiteSettings — pas de SMTP = mode console (dev).

Les **villages** sont stockés dans le modèle `Village` (même app), avec coordonnées GPS. Le champ `User.village` est une ForeignKey vers `Village`.

## Notifications

L'app `notifications` gère :
- **Notifications in-app** : modèle `Notification` avec 7 types (status_change, new_comment, assignment, new_report, new_registration, contact_form, reminder)
- **Emails HTML** : templates dans `templates/notifications/emails/` (HTML + TXT), charte Saulzet
- **Préférences** : modèle `NotificationPreference` (par utilisateur), page `/etvous/notifications/preferences/`
- **Centre de notifications** : cloche dans la navbar avec badge, dropdown, page paginée
- **Relances** : commande `send_reminders` pour les sollicitations orphelines
- **Journal d'audit** : modèle `AuditLog` pour tracer les actions (création, affectation, approbation, connexion)

Le service `notify()` dans `apps/notifications/services.py` crée la notification in-app ET envoie l'email si les préférences de l'utilisateur l'autorisent.

## État du projet

- **Version actuelle** : 1.3.5 — site déployé en production sur https://www.saulzet-le-froid.com
- Plan complet dans `saulzet-et-vous-plan-v3.md`. Prompts par phase dans `prompt-phase*-claude-code.md`.
- Toutes les phases (1 à 7) sont livrées : fondations, sollicitations, interface élus, retours utilisateurs, site communal CMS, migration de contenu, notifications/administration, mise en production.
- v1.0.0 ajoute la galerie photos, la page de mentions légales et le lien dans le footer.
- v1.1.0 ajoute le lien « Édition » dans le menu secrétaire et rend les catégories de documents dynamiques (modèle `DocumentCategory`).
- v1.2.0 correctifs de sécurité prioritaires : HSTS, CSP (middleware Django), masquage IP dans la doc, correction SITE_URL par défaut.
- v1.3.0 correctifs de sécurité court terme : rate limiting (`django-ratelimit`), sanitisation HTML CMS (`nh3`), validation des entrées, remplacement de `.extra()` par `TruncMonth`, `robots.txt`, redirection non-www → www.
- v1.3.5 protection anti-spam du formulaire de contact : honeypot, rate limiting (3/min/IP), validation temporelle (< 3s).
- Guide de déploiement : `docs/deploiement-production.md`. Script de déploiement : `scripts/deploy.sh`.
