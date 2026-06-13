# ==============================================================================
# Makefile for ContextFlow RAG Engine v2.0 Setup and Execution
# ==============================================================================

.PHONY: setup test run-backend run-frontend docker-up docker-down clean

# Create virtual environment and install packages
setup:
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Run unit tests
test:
	.venv/bin/pytest

# Start the Python FastAPI backend
run-backend:
	.venv/bin/uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Start the Streamlit frontend UI
run-frontend:
	.venv/bin/streamlit run streamlit_app/home.py

# Run docker compose in detached background mode
docker-up:
	docker compose up --build -d

# Stop docker compose services
docker-down:
	docker compose down

# Clean temporary Python cache files
clean:
	rm -rf .pytest_cache
	rm -rf .venv
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
