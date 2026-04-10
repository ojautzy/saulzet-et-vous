#!/bin/bash
# Script de déploiement Saulzet & Vous — à exécuter sur le serveur de production.
#
# Emplacement attendu : /home/saulzet/deploy.sh
# Utilisateur : saulzet (pas ubuntu, pas root)
#
# Installation initiale (depuis la machine de dev) :
#   scp scripts/deploy.sh ubuntu@<IP>:/tmp/deploy.sh
#   ssh ubuntu@<IP> 'sudo mv /tmp/deploy.sh /home/saulzet/deploy.sh \
#       && sudo chown saulzet:saulzet /home/saulzet/deploy.sh \
#       && sudo chmod +x /home/saulzet/deploy.sh'
#
# Lancement en routine (depuis la machine de dev, après git push) :
#   ssh ubuntu@<IP> 'sudo su - saulzet -c /home/saulzet/deploy.sh'
# (chemin explicite pour éviter l'expansion de ~ par le shell appelant)
#
# Voir docs/deploiement-production.md § 15 pour le contexte complet.

set -euo pipefail

cd /home/saulzet/app
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=saulzet_et_vous.settings.prod

echo "==> Fetching latest code..."
# On utilise fetch + reset --hard plutot que pull pour :
#  - rester idempotent (l'etat local est toujours exactement origin/main)
#  - survivre a toute reecriture d'historique sur origin (filter-repo, rebase)
#  - ne jamais creer de merge commit parasite en prod
git fetch origin main
git reset --hard origin/main

echo "==> Installing Python dependencies..."
pip install -q -r requirements.txt

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
