-- Create separate databases for each service
-- This prevents schema collisions between n8n, Langfuse, and Flowise

CREATE DATABASE n8n;
CREATE DATABASE langfuse;
CREATE DATABASE flowise;
