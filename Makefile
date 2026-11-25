.PHONY: up down logs test build clean

up:
	@if command -v docker > /dev/null 2>&1; then \
		docker compose up -d --build; \
		echo "Application started at http://localhost:3000 (backend: http://localhost:8000)"; \
	else \
		echo "Docker is not available in PATH."; \
		echo "To run backend: cd backend && source venv/bin/activate && uvicorn app.main:app --port 8000"; \
		echo "To run frontend: cd frontend && npm run dev"; \
	fi

down:
	@if command -v docker > /dev/null 2>&1; then \
		docker compose down; \
	else \
		echo "Docker is not running."; \
	fi

logs:
	@if command -v docker > /dev/null 2>&1; then \
		docker compose logs -f; \
	else \
		echo "Docker is not running."; \
	fi

test:
	@echo "Running backend test suite with Pytest..."
	@if [ -f "./backend/venv/bin/pytest" ]; then \
		PYTHONPATH=backend ./backend/venv/bin/pytest backend/tests/ -v -c backend/pytest.ini; \
	else \
		PYTHONPATH=backend pytest backend/tests/ -v -c backend/pytest.ini; \
	fi
