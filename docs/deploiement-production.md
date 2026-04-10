# Guide de deploiement en production — Saulzet & Vous

> **Version** : 0.9.0
> **Date** : 2026-04-08
> **Cible** : GandiCloud + OVH (DNS + mail Zimbra Pro)
> **Domaine principal** : `www.saulzet-le-froid.com`
> **Ancien domaine** : `www.saulzet-le-froid.fr` (e-monsite, a rediriger)

---

## Table des matieres

1. [Creation du serveur GandiCloud](#1-creation-du-serveur-gandicloud)
2. [Preparation du serveur](#2-preparation-du-serveur)
3. [PostgreSQL](#3-postgresql)
4. [Deploiement du code](#4-deploiement-du-code)
5. [Configuration Django (.env)](#5-configuration-django-env)
6. [Initialisation de Django](#6-initialisation-de-django)
7. [Gunicorn + Supervisor](#7-gunicorn--supervisor)
8. [Nginx](#8-nginx)
9. [DNS — pointer saulzet-le-froid.com vers GandiCloud](#9-dns--pointer-saulzet-le-froidcom-vers-gandicloud)
10. [HTTPS avec Let's Encrypt](#10-https-avec-lets-encrypt)
11. [Transfert des donnees de dev vers production](#11-transfert-des-donnees-de-dev-vers-production)
12. [Configuration email (SMTP OVH Zimbra)](#12-configuration-email-smtp-ovh-zimbra)
13. [Taches planifiees (cron)](#13-taches-planifiees-cron)
14. [Redirection de l'ancien domaine .fr vers .com](#14-redirection-de-lancien-domaine-fr-vers-com)
15. [Mises a jour futures](#15-mises-a-jour-futures)
16. [Recapitulatif de l'architecture](#16-recapitulatif-de-larchitecture)

---

## 1. Creation du serveur GandiCloud

### Choix de la configuration

| Critere | V-R1 (1 vCPU / 1 Go) | V-R2 (1 vCPU / 2 Go) |
|---|---|---|
| Django + Gunicorn + Nginx + PostgreSQL | Juste | Confortable |
| Marge pour pics / cron / backups | Non | Oui |
| Cout mensuel | ~3-4 EUR | ~6-7 EUR |

**Recommandation : V-R2** — marge suffisante pour l'ensemble de la stack sur une seule machine.

### Pas a pas dans l'interface GandiCloud

1. Se connecter sur [cloud.gandi.net](https://cloud.gandi.net)
2. Cliquer **Creer un serveur**
3. **Nom** : `saulzet-prod`
4. **Region** : FR-SD6 (France)
5. **Configuration** : **V-R2**
6. **Image OS** : **Ubuntu 24.04 LTS** (support jusqu'en 2029)
7. **Stockage** : 25 Go (le site + DB + media peseront < 1 Go)
8. **Cle SSH** : ajouter sa cle publique (`~/.ssh/id_ed25519.pub`)
   ```bash
   # Si pas de cle SSH existante :
   ssh-keygen -t ed25519 -C "olivier@saulzet"
   cat ~/.ssh/id_ed25519.pub
   ```
9. **Valider** et attendre le provisionnement (~1-2 min)
10. **Noter l'adresse IP publique** attribuee (ex : `185.x.x.x`)

---

## 2. Preparation du serveur

```bash
# Connexion (GandiCloud Ubuntu interdit root, utiliser l'utilisateur ubuntu)
ssh ubuntu@185.x.x.x

# Mise a jour systeme
sudo apt update && sudo apt upgrade -y

# Paquets necessaires
sudo apt install -y python3 python3-venv python3-pip python3-dev \
  postgresql postgresql-contrib libpq-dev \
  nginx certbot python3-certbot-nginx \
  git nodejs npm supervisor ufw

# Pare-feu
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Creer un utilisateur dedie (ne pas faire tourner le site en root)
sudo adduser --disabled-password saulzet
sudo usermod -aG sudo saulzet

# Permettre a saulzet de redemarrer Gunicorn sans mot de passe
echo 'saulzet ALL=(ALL) NOPASSWD: /usr/bin/supervisorctl restart saulzet' \
  | sudo tee /etc/sudoers.d/saulzet
sudo chmod 440 /etc/sudoers.d/saulzet
```

---

## 3. PostgreSQL

### Etape 1 : generer un mot de passe fort

```bash
openssl rand -hex 24
```

> Utiliser `-hex` (et non `-base64`) pour eviter les caracteres `+`, `/` et `=`
> qui posent probleme dans l'URL `DATABASE_URL` du fichier `.env`.

**Noter le resultat** (ex : `xK9m2pL7qR4nW8vB3jF6hT1y`) — il servira juste apres
et aussi a l'etape 5 (fichier `.env`).

### Etape 2 : creer la base et l'utilisateur

```bash
sudo -u postgres psql
```

Dans le prompt PostgreSQL, coller les commandes suivantes
**en remplacant `COLLER_LE_MOT_DE_PASSE_ICI` par le mot de passe genere a l'etape 1** :

```sql
CREATE DATABASE saulzet_db;
CREATE USER saulzet_user WITH PASSWORD 'REDACTED_DB_PASSWORD';
ALTER ROLE saulzet_user SET client_encoding TO 'utf8';
ALTER ROLE saulzet_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE saulzet_user SET timezone TO 'Europe/Paris';
GRANT ALL PRIVILEGES ON DATABASE saulzet_db TO saulzet_user;
ALTER DATABASE saulzet_db OWNER TO saulzet_user;
\q
```

---

## 4. Deploiement du code

```bash
sudo su - saulzet
mkdir -p ~/app
cd ~/app

# Cloner le repo
git clone https://github.com/ojautzy/saulzet-et-vous.git .

# Environnement Python
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Compiler le CSS Tailwind
npm ci
npm run build:css
```

---

## 5. Configuration Django (.env)

```bash
# Se connecter au serveur et basculer vers saulzet
ssh ubuntu@185.x.x.x
sudo su - saulzet

# Activer le venv et generer la cle secrete
cd ~/app
source venv/bin/activate
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Noter la cle affichee. Creer le fichier `~/app/.env`
(**remplacer** la cle secrete et le mot de passe PostgreSQL de l'etape 3) :

```bash
cat > ~/app/.env << 'EOF'
SECRET_KEY=REDACTED_SECRET_KEY
ALLOWED_HOSTS=saulzet-le-froid.com,www.saulzet-le-froid.com
CSRF_TRUSTED_ORIGINS=https://saulzet-le-froid.com,https://www.saulzet-le-froid.com
DATABASE_URL=postgres://saulzet_user:REDACTED_DB_PASSWORD@localhost:5432/saulzet_db
SITE_URL=https://www.saulzet-le-froid.com
DJANGO_SETTINGS_MODULE=saulzet_et_vous.settings.prod
EOF
```

---

## 6. Initialisation de Django

```bash
# Se connecter au serveur et basculer vers saulzet
ssh ubuntu@185.x.x.x
sudo su - saulzet

cd ~/app
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=saulzet_et_vous.settings.prod

python manage.py migrate
python manage.py collectstatic --noinput

# Creer un superuser UNIQUEMENT si vous ne prevoyez pas d'importer
# les donnees de dev a l'etape 12 (le loaddata amenera le compte admin existant).
# Sinon, sauter cette commande pour eviter un doublon :
# python manage.py createsuperuser
```

---

## 7. Gunicorn + Supervisor

```bash
# Se connecter au serveur (en tant que ubuntu pour les commandes sudo)
ssh ubuntu@185.x.x.x
```

Creer le repertoire de logs :

```bash
sudo mkdir -p /var/log/saulzet
sudo chown saulzet:saulzet /var/log/saulzet
```

Creer `/etc/supervisor/conf.d/saulzet.conf` :

```bash
sudo tee /etc/supervisor/conf.d/saulzet.conf << 'EOF'
[program:saulzet]
command=/home/saulzet/app/venv/bin/gunicorn saulzet_et_vous.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 120
directory=/home/saulzet/app
user=saulzet
environment=DJANGO_SETTINGS_MODULE="saulzet_et_vous.settings.prod"
autostart=true
autorestart=true
stdout_logfile=/var/log/saulzet/gunicorn.log
stderr_logfile=/var/log/saulzet/gunicorn-error.log
EOF
```

Activer :

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start saulzet
```

Verifier :

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/
# Doit retourner 200 ou 301
```

---

## 8. Nginx

```bash
# Se connecter au serveur
ssh ubuntu@185.x.x.x
```

Creer `/etc/nginx/sites-available/saulzet` :

```bash
sudo tee /etc/nginx/sites-available/saulzet << 'EOF'
server {
    listen 80;
    server_name saulzet-le-froid.com www.saulzet-le-froid.com;

    client_max_body_size 10M;

    location /static/ {
        alias /home/saulzet/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/saulzet/app/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

Activer :

```bash
sudo ln -s /etc/nginx/sites-available/saulzet /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

Rendre les fichiers statiques et media lisibles par Nginx (`www-data`) :

```bash
sudo chmod 755 /home/saulzet
sudo chmod -R 755 /home/saulzet/app/staticfiles/
sudo chmod -R 755 /home/saulzet/app/media/
```

---

## 9. DNS — pointer saulzet-le-froid.com vers GandiCloud

Dans l'**espace client OVH** > **Noms de domaine** > `saulzet-le-froid.com` > **Zone DNS** :

| Type | Sous-domaine | Cible | TTL |
|---|---|---|---|
| A | *(vide = @)* | `185.x.x.x` | 3600 |
| A | `www` | `185.x.x.x` | 3600 |

> **Ne pas toucher aux enregistrements MX** — ils gerent le mail Zimbra Pro.

Verification (apres propagation, quelques minutes a quelques heures) :

```bash
dig +short saulzet-le-froid.com
dig +short www.saulzet-le-froid.com
# Doivent retourner 185.x.x.x
```

---

## 10. HTTPS avec Let's Encrypt

Une fois le DNS propage :

```bash
# Se connecter au serveur
ssh ubuntu@185.x.x.x

sudo certbot --nginx -d saulzet-le-froid.com -d www.saulzet-le-froid.com
```

Certbot va :
- Obtenir le certificat
- Modifier automatiquement la configuration Nginx (ecoute 443, redirection 80 -> 443)
- Configurer le renouvellement automatique (timer systemd)

Verification :

```bash
curl -I https://www.saulzet-le-froid.com
```

---

## 11. Transfert des donnees de dev vers production

> **Pourquoi cette etape avant la configuration email ?**
> Le compte administrateur Django est importe avec les donnees de dev.
> Il faut donc importer les donnees avant de pouvoir acceder a l'admin
> pour configurer le SMTP.

### 11.1 Export depuis la machine de dev

```bash
cd "/Users/olivier/Documents/Claude Code/saulzet-et-vous"
source venv/bin/activate

# Exporter toutes les donnees
# On exclut les tables auto-generees (contenttypes, permissions)
# et NotificationPreference (recree automatiquement par un signal post_save User)
python manage.py dumpdata \
  --natural-foreign --natural-primary \
  --exclude contenttypes \
  --exclude auth.permission \
  --exclude admin.logentry \
  --exclude sessions \
  --exclude notifications.notificationpreference \
  --indent 2 \
  -o data_export.json
```

### 11.2 Copier vers le serveur

Depuis la machine de dev, copier vers le home de `ubuntu`
(on ne peut pas se connecter directement en `saulzet` via SSH) :

```bash
scp data_export.json ubuntu@185.x.x.x:/tmp/
rsync -avz --progress media/ ubuntu@92.243.27.159:/tmp/media_upload/
```

Puis sur le serveur, deplacer vers le repertoire de saulzet :

```bash
ssh ubuntu@185.x.x.x

sudo cp /tmp/data_export.json /home/saulzet/app/
sudo mkdir -p /home/saulzet/app/media
sudo cp -r /tmp/media_upload/* /home/saulzet/app/media/
sudo chown -R saulzet:saulzet /home/saulzet/app/data_export.json /home/saulzet/app/media/
sudo chmod -R 755 /home/saulzet/app/media/
rm -rf /tmp/data_export.json /tmp/media_upload
```

### 11.3 Charger sur le serveur de production

```bash
# Se connecter au serveur et basculer vers saulzet
ssh ubuntu@185.x.x.x
sudo su - saulzet

cd ~/app && source venv/bin/activate
export DJANGO_SETTINGS_MODULE=saulzet_et_vous.settings.prod

# Charger les donnees
python manage.py loaddata data_export.json
```

> **Si `loaddata` echoue** sur des problemes de dependances, exporter app par app :
> ```bash
> python manage.py dumpdata settings_app accounts pages reports notifications \
>   --natural-foreign --natural-primary \
>   --exclude contenttypes --exclude auth.permission \
>   --indent 2 -o data_export.json
> ```

> **Important** : apres le chargement, verifier que le `SiteSettings` pointe
> bien vers `https://www.saulzet-le-froid.com` (et non `saulzet.jautzy.com`).
> Mettre a jour dans l'admin si necessaire.

---

## 12. Configuration email (SMTP OVH Zimbra)

Se connecter a l'admin Django (`https://www.saulzet-le-froid.com/admin/`)
avec le compte administrateur importe a l'etape precedente,
et configurer dans **SiteSettings** :

| Champ | Valeur |
|---|---|
| Email expediteur | `noreply@saulzet-le-froid.com` |
| Email contact | `contact@saulzet-le-froid.com` |
| Hote SMTP | `pro1.mail.ovh.net` |
| Port SMTP | `587` |
| TLS | Oui |
| Utilisateur SMTP | `noreply@saulzet-le-froid.com` |
| Mot de passe SMTP | *(mot de passe du compte Zimbra)* |

> L'hote SMTP exact est visible dans l'espace OVH > **Emails** > **Configuration**.
> Ce sera `pro1.mail.ovh.net` ou `pro2.mail.ovh.net` selon le cluster.

Pour tester :

```bash
# Se connecter au serveur et basculer vers saulzet
ssh ubuntu@185.x.x.x
sudo su - saulzet

cd ~/app && source venv/bin/activate
export DJANGO_SETTINGS_MODULE=saulzet_et_vous.settings.prod
python manage.py shell -c "
from django.core.mail import send_mail
from apps.settings_app.models import SiteSettings
config = SiteSettings.load()
send_mail('Test', 'Ceci est un test.', config.from_email, ['votre@email.com'])
"
```

---

## 13. Taches planifiees (cron)

```bash
# Se connecter au serveur et basculer vers saulzet
ssh ubuntu@185.x.x.x
sudo su - saulzet

crontab -e
```

Ajouter :

```cron
# Relances sollicitations orphelines — tous les jours a 8h
0 8 * * * cd /home/saulzet/app && /home/saulzet/app/venv/bin/python manage.py send_reminders --settings=saulzet_et_vous.settings.prod >> /var/log/saulzet/reminders.log 2>&1
```

---

## 14. Redirection de l'ancien domaine .fr vers .com

L'objectif : tout internaute visitant `www.saulzet-le-froid.fr` (heberge actuellement chez e-monsite) est redirige automatiquement vers `https://www.saulzet-le-froid.com`.

Il y a **trois strategies possibles**, selon le niveau de controle que l'on a sur le .fr.

### Strategie A — Redirection via e-monsite (le plus simple)

Si e-monsite propose une option de redirection dans son panneau d'administration :

1. Se connecter au back-office e-monsite
2. Chercher une option **Redirection 301** ou **Redirection de domaine**
3. Configurer la redirection vers `https://www.saulzet-le-froid.com`

> C'est la solution la plus rapide si e-monsite la propose.
> Verifier dans les parametres du site ou contacter leur support.

### Strategie B — Transferer le DNS du .fr vers OVH et rediriger (recommande)

C'est la meilleure solution a moyen terme : on prend le controle du .fr chez OVH et on configure une redirection permanente.

#### Etape 1 : Transferer le domaine .fr vers OVH

1. Chez e-monsite / le registrar actuel du .fr :
   - Deverrouiller le domaine
   - Recuperer le **code de transfert** (code AUTH / EPP)
2. Chez OVH :
   - Aller dans **Commander** > **Transferer un domaine**
   - Saisir `saulzet-le-froid.fr`
   - Coller le code de transfert
   - Valider (~5-7 jours de delai)

#### Etape 2 : Configurer la redirection dans la zone DNS OVH du .fr

Une fois le .fr transfere chez OVH, dans **Noms de domaine** > `saulzet-le-froid.fr` > **Zone DNS** :

**Option 2a — Redirection web OVH (le plus simple) :**

1. Aller dans l'onglet **Redirection**
2. Ajouter une redirection :
   - Source : `saulzet-le-froid.fr` (et `www.saulzet-le-froid.fr`)
   - Destination : `https://www.saulzet-le-froid.com`
   - Type : **Permanente (301)**

OVH s'occupe de tout (serveur web intermediaire, certificat).

**Option 2b — Via un server block Nginx sur le serveur GandiCloud :**

1. Faire pointer le .fr vers le serveur Gandi :

   | Type | Sous-domaine | Cible | TTL |
   |---|---|---|---|
   | A | *(vide = @)* | `185.x.x.x` | 3600 |
   | A | `www` | `185.x.x.x` | 3600 |

2. Ajouter un server block Nginx sur le serveur (`/etc/nginx/sites-available/saulzet-redirect-fr`) :

   ```nginx
   server {
       listen 80;
       server_name saulzet-le-froid.fr www.saulzet-le-froid.fr;
       return 301 https://www.saulzet-le-froid.com$request_uri;
   }
   ```

3. Activer et obtenir un certificat :

   ```bash
   sudo ln -s /etc/nginx/sites-available/saulzet-redirect-fr /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   sudo certbot --nginx -d saulzet-le-froid.fr -d www.saulzet-le-froid.fr
   ```

   Certbot transformera le bloc en :

   ```nginx
   server {
       listen 443 ssl;
       server_name saulzet-le-froid.fr www.saulzet-le-froid.fr;
       ssl_certificate /etc/letsencrypt/live/saulzet-le-froid.fr/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/saulzet-le-froid.fr/privkey.pem;
       return 301 https://www.saulzet-le-froid.com$request_uri;
   }

   server {
       listen 80;
       server_name saulzet-le-froid.fr www.saulzet-le-froid.fr;
       return 301 https://www.saulzet-le-froid.com$request_uri;
   }
   ```

### Strategie C — Page de redirection temporaire chez e-monsite

En attendant le transfert du .fr, si e-monsite permet d'editer le contenu HTML :

1. Remplacer le contenu de la page d'accueil par :

   ```html
   <!DOCTYPE html>
   <html lang="fr">
   <head>
       <meta charset="utf-8">
       <meta http-equiv="refresh" content="0;url=https://www.saulzet-le-froid.com">
       <title>Saulzet-le-Froid - Nouveau site</title>
   </head>
   <body>
       <p>Le site de Saulzet-le-Froid a demenage.
          <a href="https://www.saulzet-le-froid.com">Cliquez ici</a>
          si vous n'etes pas redirige automatiquement.</p>
   </body>
   </html>
   ```

> **Attention** : `<meta http-equiv="refresh">` n'est pas une vraie 301.
> Les moteurs de recherche ne la traitent pas toujours comme une redirection permanente.
> C'est un palliatif en attendant la strategie B.

### Recommandation

| Phase | Action |
|---|---|
| **Immediatement** | Strategie C — page de redirection chez e-monsite |
| **Sous 1-2 semaines** | Strategie B — lancer le transfert du .fr vers OVH |
| **Apres transfert** | Option 2a (redirection OVH) ou 2b (Nginx) au choix |

---

## 15. Mises a jour futures

### Script de deploiement

Le script prêt à l'emploi est versionné dans le dépôt : [`scripts/deploy.sh`](../scripts/deploy.sh).

**Installation initiale** (une seule fois, depuis la machine de dev) :

```bash
scp scripts/deploy.sh ubuntu@185.x.x.x:/tmp/deploy.sh
ssh ubuntu@185.x.x.x 'sudo mv /tmp/deploy.sh /home/saulzet/deploy.sh \
    && sudo chown saulzet:saulzet /home/saulzet/deploy.sh \
    && sudo chmod +x /home/saulzet/deploy.sh'
```

<details>
<summary>Ou, pour référence, créer le script manuellement sur le serveur</summary>

```bash
# Se connecter au serveur et basculer vers saulzet
ssh ubuntu@185.x.x.x
sudo su - saulzet
```

Creer `/home/saulzet/deploy.sh` :

```bash
cat > ~/deploy.sh << 'SCRIPT'
#!/bin/bash
set -e

cd /home/saulzet/app
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=saulzet_et_vous.settings.prod

echo "==> Pulling latest code..."
git pull origin main

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Building CSS..."
npm ci --silent
npm run build:css

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Restarting Gunicorn..."
sudo supervisorctl restart saulzet

echo "==> Done! Version: $(cat VERSION)"
SCRIPT
chmod +x ~/deploy.sh
```

</details>

### Utilisation au quotidien

Depuis la machine de dev :

```bash
# 1. Committer et pousser
git push origin main

# 2. Deployer (se connecte en ubuntu, bascule en saulzet, lance le script)
ssh ubuntu@185.x.x.x 'sudo su - saulzet -c ~/deploy.sh'
```

### Variante rapide (sans rebuild CSS)

Si seul du code Python/templates a change, un deploiement plus rapide :

```bash
ssh ubuntu@185.x.x.x 'sudo su - saulzet -c "cd ~/app && git pull && source venv/bin/activate && python manage.py migrate --noinput && python manage.py collectstatic --noinput && sudo supervisorctl restart saulzet"'
```

### Transferts de donnees supplementaires

Pour re-synchroniser les media (nouvelles images, documents PDF) :

```bash
rsync -avz --progress media/ ubuntu@185.x.x.x:/tmp/media_upload/
ssh ubuntu@185.x.x.x 'sudo cp -r /tmp/media_upload/* /home/saulzet/app/media/ && sudo chown -R saulzet:saulzet /home/saulzet/app/media/ && rm -rf /tmp/media_upload'
```

---

## 16. Recapitulatif de l'architecture

```
Internet
  |
  |-- DNS OVH : saulzet-le-froid.com  --> IP GandiCloud
  |-- DNS OVH : saulzet-le-froid.fr   --> redirection 301 vers .com
  |-- MX OVH  : Zimbra Pro (inchange)
  |
  +-- GandiCloud V-R2 (Ubuntu 24.04 LTS)
       |
       |-- Nginx (ports 443/80)
       |     |-- HTTPS : Let's Encrypt (certbot auto-renew)
       |     |-- /static/  -->  /home/saulzet/app/staticfiles/
       |     |-- /media/   -->  /home/saulzet/app/media/
       |     |-- /         -->  reverse proxy --> Gunicorn :8000
       |     +-- *.saulzet-le-froid.fr --> 301 vers .com
       |
       |-- Gunicorn (127.0.0.1:8000, 2 workers)
       |     +-- Django 5.2 (settings.prod)
       |
       |-- PostgreSQL (local)
       |     +-- saulzet_db
       |
       |-- Supervisor (gere Gunicorn)
       |
       |-- Cron
       |     +-- send_reminders (quotidien, 8h)
       |
       +-- SMTP sortant --> OVH Zimbra Pro
             +-- noreply@saulzet-le-froid.com
```

---

## Checklist de mise en production

- [ ] Serveur GandiCloud cree (V-R2, Ubuntu 24.04)
- [ ] Paquets systeme installes
- [ ] Utilisateur `saulzet` cree
- [ ] PostgreSQL configure
- [ ] Code clone et environnement Python pret
- [ ] CSS Tailwind compile
- [ ] Fichier `.env` configure
- [ ] `migrate` + `collectstatic` + `createsuperuser` executes
- [ ] Gunicorn / Supervisor fonctionnel
- [ ] Nginx configure et actif
- [ ] DNS .com pointe vers le serveur
- [ ] Certificat HTTPS obtenu (certbot)
- [ ] Donnees de dev importees (loaddata + rsync media)
- [ ] SiteSettings : SMTP configure dans l'admin
- [ ] SiteSettings : SITE_URL mis a jour vers `https://www.saulzet-le-froid.com`
- [ ] Cron `send_reminders` configure
- [ ] Redirection .fr vers .com en place
- [ ] Script `deploy.sh` cree et teste
- [ ] Test complet : navigation, login, creation sollicitation, envoi email
