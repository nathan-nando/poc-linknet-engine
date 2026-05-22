.PHONY: up down build logs migrate restart

# Start engine and database
up:
	docker-compose up -d

# Stop and remove engine and database containers
down:
	docker-compose down

# Rebuild engine image and start
build:
	docker-compose up -d --build

# View logs
logs:
	docker-compose logs -f

# Run the YAML to DB migration script inside the engine container
migrate:
	docker-compose exec engine python scripts/migrate_thresholds.py

# Export YOLO model to ONNX format (for CI/CD or manual optimization)
export-onnx:
	docker-compose exec engine python scripts/export_onnx.py

# Restart engine services
restart:
	docker-compose restart
