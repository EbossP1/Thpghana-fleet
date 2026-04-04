#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# THP Ghana Fleet Management — Let's Encrypt SSL Setup
# Run this on your production server after DNS is configured
# ─────────────────────────────────────────────────────────────────
set -e

DOMAIN="${1:-fleet.thpghana.org}"
EMAIL="${2:-it@thp-ghana.org}"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   SSL Certificate Setup (Let's Encrypt)                 ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║   Domain: $DOMAIN"
echo "║   Email:  $EMAIL"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Install certbot ──────────────────────────────────────
if ! command -v certbot &>/dev/null; then
    echo "▸ Installing certbot..."
    apt-get update && apt-get install -y certbot
fi

# ── 2. Create webroot directory ──────────────────────────────
mkdir -p /var/www/certbot

# ── 3. Temporarily switch nginx to HTTP-only for challenge ───
echo "▸ Requesting certificate..."
# Stop nginx to free port 80 for standalone mode
docker compose stop nginx 2>/dev/null || true

certbot certonly --standalone \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --preferred-challenges http

# ── 4. Copy certs to nginx ssl directory ─────────────────────
echo "▸ Installing certificate..."
mkdir -p nginx/ssl
cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" nginx/ssl/fullchain.pem
cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" nginx/ssl/privkey.pem
chmod 600 nginx/ssl/privkey.pem

# ── 5. Restart nginx ────────────────────────────────────────
echo "▸ Restarting nginx with new certificate..."
docker compose up -d nginx

# ── 6. Set up auto-renewal ──────────────────────────────────
echo "▸ Setting up auto-renewal cron..."
CRON_CMD="0 3 * * * certbot renew --quiet --deploy-hook 'cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $(pwd)/nginx/ssl/ && cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $(pwd)/nginx/ssl/ && docker compose -f $(pwd)/docker-compose.yml restart nginx'"

(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_CMD") | crontab -

echo ""
echo "✅ SSL certificate installed successfully!"
echo "   Auto-renewal is configured (daily check at 3 AM)"
echo "   Test: https://$DOMAIN"
