#!/bin/bash
# =============================================================================
# nops.no / ByggSjekk – Produksjons-deploy
#
# Bruk: ./deploy.sh [server-ip]
# Eks:  ./deploy.sh 168.119.xxx.xxx
#
# Forutsetninger:
# - SSH-tilgang til serveren (ssh root@server-ip)
# - Docker og Docker Compose installert på serveren
# - Domene nops.no peker til server-IP (A-record)
# =============================================================================

set -e

SERVER_IP="${1:-}"
DOMAIN="nops.no"
APP_DIR="/opt/nops"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ -z "$SERVER_IP" ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║         nops.no / ByggSjekk – Deploy Guide          ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "STEG 1: Bestill en VPS"
    echo "  Anbefalt: Hetzner Cloud CPX21 (3 vCPU, 4 GB RAM, 80 GB) – ca. 120 kr/mnd"
    echo "  Alternativ: DigitalOcean Droplet, Vultr, Linode"
    echo "  OS: Ubuntu 24.04 LTS"
    echo ""
    echo "STEG 2: Pek domenet"
    echo "  Logg inn hos domeneregistrar og sett:"
    echo "  A-record:  nops.no      → <server-ip>"
    echo "  A-record:  www.nops.no  → <server-ip>"
    echo ""
    echo "STEG 3: Kjør dette skriptet"
    echo "  ./deploy.sh <server-ip>"
    echo ""
    echo "STEG 4: Konfigurer Stripe webhook"
    echo "  Dashboard → Webhooks → Legg til endpoint:"
    echo "  URL: https://nops.no/api/v1/billing/webhook"
    echo "  Events: checkout.session.completed,"
    echo "          customer.subscription.updated,"
    echo "          customer.subscription.deleted"
    echo ""
    echo "STEG 5: Verifiser"
    echo "  https://nops.no          → Landingsside"
    echo "  https://nops.no/pricing  → Priser"
    echo "  https://nops.no/register → Registrering"
    echo ""
    exit 0
fi

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Deployer nops.no til $SERVER_IP                     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── STEG 1: Installer Docker på serveren ────────────────────
echo "→ Steg 1/5: Installerer Docker på serveren..."
ssh root@"$SERVER_IP" << 'INSTALL_DOCKER'
if ! command -v docker &> /dev/null; then
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable docker
    echo "Docker installert."
else
    echo "Docker allerede installert."
fi
# Installer certbot
if ! command -v certbot &> /dev/null; then
    apt-get install -y -qq certbot
    echo "Certbot installert."
fi
INSTALL_DOCKER

# ── STEG 2: Kopier prosjektet ──────────────────────────────
echo "→ Steg 2/5: Kopierer prosjektet til serveren..."
ssh root@"$SERVER_IP" "mkdir -p $APP_DIR"
rsync -az --progress --exclude='.git' --exclude='node_modules' --exclude='.next' --exclude='__pycache__' --exclude='.env' \
    "$REPO_DIR/" root@"$SERVER_IP":"$APP_DIR/"

# Kopier .env separat
scp "$REPO_DIR/.env" root@"$SERVER_IP":"$APP_DIR/.env"

# Oppdater .env for produksjon
ssh root@"$SERVER_IP" << ENVFIX
cd $APP_DIR
sed -i 's|NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=https://$DOMAIN|' .env
sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=["https://$DOMAIN","https://www.$DOMAIN"]|' .env
sed -i 's|NOPS_BASE_URL=.*|NOPS_BASE_URL=https://$DOMAIN|' .env
sed -i 's|DEBUG=.*|DEBUG=false|' .env
sed -i 's|ENVIRONMENT=.*|ENVIRONMENT=production|' .env
echo ".env oppdatert for produksjon."
ENVFIX

# ── STEG 3: SSL-sertifikat ─────────────────────────────────
echo "→ Steg 3/5: Henter SSL-sertifikat..."
ssh root@"$SERVER_IP" << SSL
if [ ! -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem ]; then
    # Stopp evt. Docker som bruker port 80
    docker compose -f $APP_DIR/infra/docker-compose.yml down 2>/dev/null || true
    certbot certonly --standalone -d $DOMAIN -d www.$DOMAIN --email hey@nops.no --agree-tos --no-eff-email --non-interactive
    echo "SSL-sertifikat hentet."
else
    echo "SSL-sertifikat eksisterer allerede."
fi
# Sett opp auto-fornyelse
echo "0 3 * * * certbot renew --quiet && docker compose -f $APP_DIR/infra/docker-compose.yml -f $APP_DIR/infra/docker-compose.prod.yml exec nginx nginx -s reload 2>/dev/null" | crontab -
SSL

# ── STEG 4: Bygg og start ──────────────────────────────────
echo "→ Steg 4/5: Bygger og starter tjenestene..."
ssh root@"$SERVER_IP" << BUILD
cd $APP_DIR
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml up -d --build
echo "Venter på at tjenestene starter..."
sleep 15
# Kjør database-migrasjoner
docker compose -f infra/docker-compose.yml -f infra/docker-compose.prod.yml exec -T api alembic upgrade head 2>/dev/null || echo "Migrasjoner hoppet over (ok ved første deploy)"
BUILD

# ── STEG 5: Verifiser ──────────────────────────────────────
echo "→ Steg 5/5: Verifiserer..."
sleep 5
echo ""
echo "Sjekker helse..."
if curl -sf "https://$DOMAIN/health" > /dev/null 2>&1; then
    echo "  ✅ API: OK"
else
    echo "  ⚠️  API: Ikke tilgjengelig ennå (kan ta noen minutter)"
fi
if curl -sf "https://$DOMAIN" > /dev/null 2>&1; then
    echo "  ✅ Web: OK"
else
    echo "  ⚠️  Web: Ikke tilgjengelig ennå (kan ta noen minutter)"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║              Deploy fullført!                        ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║                                                      ║"
echo "║  🌐 https://nops.no                                  ║"
echo "║  📊 https://nops.no/landing                          ║"
echo "║  💰 https://nops.no/pricing                          ║"
echo "║                                                      ║"
echo "║  Neste steg:                                         ║"
echo "║  1. Konfigurer Stripe webhook                        ║"
echo "║  2. Registrer en testkonto                           ║"
echo "║  3. Søk opp en eiendom                               ║"
echo "║  4. Del nops.no/landing på LinkedIn                  ║"
echo "║                                                      ║"
echo "╚══════════════════════════════════════════════════════╝"
