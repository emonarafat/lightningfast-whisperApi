# Makefile for lightningfast-whisperApi

PROJECT_NAME=whisper-api
COMPOSE=docker-compose

.PHONY: dev prod down build clean

dev:
    @echo "🧪 Starting development environment..."
    $(COMPOSE) --env-file .env.development -f docker-compose.yml -f docker-compose.override.yml up --build

prod:
    @echo "🚀 Starting production environment..."
    $(COMPOSE) --env-file .env.production -f docker-compose.yml up --build -d

down:
    @echo "🛑 Stopping containers..."
    $(COMPOSE) down

build:
    @echo "🔨 Rebuilding Docker images..."
    $(COMPOSE) build

clean:
    @echo "🧼 Removing containers, images, volumes..."
    $(COMPOSE) down -v --rmi all --remove-orphans
	@echo "🗑️ Cleaning up dangling images..."