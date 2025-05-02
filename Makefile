.PHONY: all setup test lint format clean docker-build docker-run deploy-dev deploy-staging deploy-prod

# Environment variables
CONTAINER_NAME = rag-api
TAG = latest

all: clean setup test lint format

setup:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	python -m spacy download en_core_web_sm

test:
	python -m pytest tests/ -v --cov=rag_system --cov-report=term --cov-report=xml

lint:
	flake8 rag_system/ tests/
	mypy rag_system/

format:
	black rag_system/ tests/
	isort rag_system/ tests/

clean:
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf __pycache__
	rm -rf rag_system/__pycache__
	rm -rf tests/__pycache__
	rm -rf dist
	rm -rf build

docker-build:
	docker build -t $(CONTAINER_NAME):$(TAG) .

docker-run:
	docker run -p 8000:8000 --name $(CONTAINER_NAME) $(CONTAINER_NAME):$(TAG)

docker-stop:
	docker stop $(CONTAINER_NAME)
	docker rm $(CONTAINER_NAME)

alembic-init:
	alembic init alembic

alembic-revision:
	alembic revision --autogenerate -m "$(message)"

alembic-upgrade:
	alembic upgrade head

deploy-dev:
	@echo "Deploying to development environment..."
	cd deployment && ./deploy.sh dev

deploy-staging:
	@echo "Deploying to staging environment..."
	cd deployment && ./deploy.sh staging

deploy-prod:
	@echo "Deploying to production environment..."
	cd deployment && ./deploy.sh prod