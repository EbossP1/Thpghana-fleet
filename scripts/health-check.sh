#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# THP Ghana Fleet Management — Health Check / Status
# Usage: ./health-check.sh
# ─────────────────────────────────────────────────────────────────

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   THP Ghana Fleet Management — System Status            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

check_service() {
    local name="$1"
    local status=$(docker compose ps --format json "$name" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health','') or d.get('State',''))" 2>/dev/null || echo "unknown")
    if echo "$status" | grep -qi "healthy\|running"; then
        echo -e "  ${GREEN}✅${NC} $name: $status"
    elif echo "$status" | grep -qi "starting"; then
        echo -e "  ${YELLOW}⏳${NC} $name: $status"
    else
        echo -e "  ${RED}❌${NC} $name: $status"
    fi
}

echo "Docker Services:"
check_service "db"
check_service "app"
check_service "nginx"
check_service "backup"

echo ""
echo "Endpoints:"

# App server
if curl -sf http://localhost:8000/ >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅${NC} App server (http://localhost:8000)"
else
    echo -e "  ${RED}❌${NC} App server (http://localhost:8000)"
fi

# Nginx HTTP
if curl -sf http://localhost/ >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅${NC} Nginx HTTP (http://localhost)"
else
    echo -e "  ${YELLOW}↩️${NC}  Nginx HTTP (redirects to HTTPS — normal)"
fi

# Nginx HTTPS
if curl -sf -k https://localhost/ >/dev/null 2>&1; then
    echo -e "  ${GREEN}✅${NC} Nginx HTTPS (https://localhost)"
else
    echo -e "  ${RED}❌${NC} Nginx HTTPS (https://localhost)"
fi

echo ""
echo "Database:"
DB_SIZE=$(docker compose exec -T db psql -U fleetuser -d fleetdb -t -c "SELECT pg_size_pretty(pg_database_size('fleetdb'));" 2>/dev/null | xargs)
DB_VEHICLES=$(docker compose exec -T db psql -U fleetuser -d fleetdb -t -c "SELECT COUNT(*) FROM vehicles WHERE is_active=true;" 2>/dev/null | xargs)
DB_DRIVERS=$(docker compose exec -T db psql -U fleetuser -d fleetdb -t -c "SELECT COUNT(*) FROM drivers WHERE is_active=true;" 2>/dev/null | xargs)
DB_CONNECTIONS=$(docker compose exec -T db psql -U fleetuser -d fleetdb -t -c "SELECT COUNT(*) FROM pg_stat_activity WHERE datname='fleetdb';" 2>/dev/null | xargs)

echo "  Database size:     ${DB_SIZE:-unknown}"
echo "  Active vehicles:   ${DB_VEHICLES:-unknown}"
echo "  Active drivers:    ${DB_DRIVERS:-unknown}"
echo "  DB connections:    ${DB_CONNECTIONS:-unknown}"

echo ""
echo "Backups:"
LATEST=$(ls -t backups/fleet_*.dump 2>/dev/null | head -1)
BACKUP_COUNT=$(ls backups/fleet_*.dump 2>/dev/null | wc -l)
if [ -n "$LATEST" ]; then
    LATEST_SIZE=$(du -h "$LATEST" | cut -f1)
    LATEST_DATE=$(stat -c %y "$LATEST" 2>/dev/null | cut -d. -f1)
    echo "  Total backups:     $BACKUP_COUNT"
    echo "  Latest:            $(basename $LATEST) ($LATEST_SIZE)"
    echo "  Created:           $LATEST_DATE"
else
    echo "  No backups found"
fi

echo ""
echo "Disk:"
echo "  $(df -h / | tail -1 | awk '{print "Used: "$3" / "$2" ("$5" used)"}')"
DOCKER_SIZE=$(docker system df --format '{{.Size}}' 2>/dev/null | head -1)
echo "  Docker images:     ${DOCKER_SIZE:-unknown}"

echo ""
echo "SSL Certificate:"
CERT_FILE="nginx/ssl/fullchain.pem"
if [ -f "$CERT_FILE" ]; then
    EXPIRY=$(openssl x509 -enddate -noout -in "$CERT_FILE" 2>/dev/null | cut -d= -f2)
    ISSUER=$(openssl x509 -issuer -noout -in "$CERT_FILE" 2>/dev/null | sed 's/issuer=//')
    if [ -n "$EXPIRY" ]; then
        EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null)
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
        if [ "$DAYS_LEFT" -gt 30 ]; then
            echo -e "  ${GREEN}✅${NC} Expires: $EXPIRY ($DAYS_LEFT days)"
        elif [ "$DAYS_LEFT" -gt 0 ]; then
            echo -e "  ${YELLOW}⚠️${NC}  Expires: $EXPIRY ($DAYS_LEFT days — renew soon!)"
        else
            echo -e "  ${RED}❌${NC} EXPIRED: $EXPIRY"
        fi
        echo "  Issuer: $ISSUER"
    fi
else
    echo -e "  ${RED}❌${NC} No certificate found"
fi

echo ""
