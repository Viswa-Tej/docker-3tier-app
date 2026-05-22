.PHONY: up down restart logs ps clean help

help:           ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' Makefile | awk 'BEGIN{FS=":.*##"}{printf "  %-12s %s\n",$$1,$$2}'

up:             ## Start all services (build if needed)
	cp -n .env.example .env 2>/dev/null || true
	docker-compose up --build -d
	@echo ""
	@echo "App running at http://localhost:8080"

down:           ## Stop and remove containers (keeps data)
	docker-compose down

restart:        ## Restart all services
	docker-compose restart

logs:           ## Tail logs from all services
	docker-compose logs -f

logs-api:       ## Tail API logs only
	docker-compose logs -f api

ps:             ## Show running containers and their health
	docker-compose ps

clean:          ## Stop containers AND delete all data volumes
	docker-compose down -v
	@echo "All containers and volumes removed."

health:         ## Check health of all services
	@echo "=== Container Status ===" && docker-compose ps
	@echo "" && echo "=== API Health ===" && curl -s http://localhost:8080/health | python3 -m json.tool
