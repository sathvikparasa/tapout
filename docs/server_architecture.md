# Server Architecture
This is a brief overview of the backend structure for the server that the iOS and Android clients will communicate with.

## Modules
Python FastAPI backend with an async scheduler that queries DB for updates routinely.

Supabase postgres SQL database that can be configured in the .env file with a connection string.

## Deliverables
Endpoints that an iOS and Android client can connect to.

A server that can be hosted on GCP App Engine.