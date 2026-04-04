#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Generate self-signed SSL certs for development/testing
# For production, use Let's Encrypt (see deploy guide)
# ─────────────────────────────────────────────────────────────────
set -e

CERT_DIR="$(dirname "$0")/nginx/ssl"
mkdir -p "$CERT_DIR"

echo "Generating self-signed SSL certificate..."
openssl req -x509 -nodes -days 365 \
    -newkey rsa:2048 \
    -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" \
    -subj "/C=GH/ST=Greater Accra/L=Accra/O=THP Ghana/OU=Fleet Management/CN=fleet.thpghana.org"

echo "✅ SSL certificates generated in $CERT_DIR"
echo "   Certificate: $CERT_DIR/fullchain.pem"
echo "   Private Key: $CERT_DIR/privkey.pem"
echo ""
echo "⚠️  These are self-signed certs for DEVELOPMENT ONLY."
echo "   For production, use Let's Encrypt:"
echo "   sudo certbot certonly --webroot -w /var/www/certbot -d fleet.thpghana.org"
