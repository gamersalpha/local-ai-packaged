#!/bin/sh
# Generate config.js from environment variables at container startup
set -e

IP="${SERVER_IP:-127.0.0.1}"
DOMAIN="${BASE_DOMAIN:-}"

cat > /usr/share/nginx/html/config.js << JSEOF
window.__CONFIG__ = {
  baseDomain: "${DOMAIN}",
  services: {
    ollama:    { url: "${OLLAMA_HOSTNAME:+https://$OLLAMA_HOSTNAME}",    local: "http://${IP}:11434" },
    openwebui: { url: "${WEBUI_HOSTNAME:+https://$WEBUI_HOSTNAME}",     local: "http://${IP}:8080" },
    n8n:       { url: "${N8N_HOSTNAME:+https://$N8N_HOSTNAME}",         local: "http://${IP}:5678" },
    flowise:   { url: "${FLOWISE_HOSTNAME:+https://$FLOWISE_HOSTNAME}", local: "http://${IP}:3001" },
    qdrant:    { url: "${QDRANT_HOSTNAME:+https://$QDRANT_HOSTNAME}",   local: "http://${IP}:6333" },
    neo4j:     { url: "${NEO4J_HOSTNAME:+https://$NEO4J_HOSTNAME}",     local: "http://${IP}:7474" },
    langfuse:  { url: "${LANGFUSE_HOSTNAME:+https://$LANGFUSE_HOSTNAME}", local: "http://${IP}:3100" },
    searxng:   { url: "${SEARXNG_HOSTNAME:+https://$SEARXNG_HOSTNAME}", local: "http://${IP}:8081" },
    unsloth:   { url: "${UNSLOTH_HOSTNAME:+https://$UNSLOTH_HOSTNAME}", local: "http://${IP}:8888" },
    supabase:  { url: "${SUPABASE_HOSTNAME:+https://$SUPABASE_HOSTNAME}", local: "http://${IP}:8000" },
    comfyui:   { url: "${COMFYUI_HOSTNAME:+https://$COMFYUI_HOSTNAME}", local: "" }
  }
};
JSEOF

echo "config.js generated (BASE_DOMAIN=${DOMAIN:-none}, IP=${IP})"

exec nginx -g 'daemon off;'
