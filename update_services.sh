#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-cpu}"

echo "========================================="
echo "  Local AI Packaged — Update Services"
echo "========================================="
echo "Profile: $PROFILE"
echo ""

echo "🛑 Stopping services..."
docker compose -p localai -f docker-compose.yml --profile "$PROFILE" down

echo ""
echo "⬇️  Pulling latest images..."
docker compose -p localai -f docker-compose.yml --profile "$PROFILE" pull

echo ""
echo "🚀 Restarting services..."
python3 start_services.py --profile "$PROFILE" --update

echo ""
echo "✅ Update complete!"
