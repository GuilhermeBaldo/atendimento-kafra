# Define variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_FILE = docker-compose.yml

# Targets
.PHONY: build-backend run-backend build-frontend run-frontend build run stop

build-backend:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) build backend

run-backend:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up backend

stop-backend:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) stop backend

build-frontend:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) build frontend

run-frontend:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up frontend

stop-frontend:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) stop frontend

build: build-backend build-frontend

run:
	$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) up

stop: stop-frontend stop-backend
