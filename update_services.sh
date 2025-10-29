# Stop all services
docker compose -p localai -f docker-compose.yml --profile cpu  down

# Pull latest versions of all containers
docker compose -p localai -f docker-compose.yml --profile cpu  pull

# Start services again with your desired profile
python3 start_services.py --profile cpu --no-caddy
