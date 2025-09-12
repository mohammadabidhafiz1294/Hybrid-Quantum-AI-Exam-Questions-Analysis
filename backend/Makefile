# EduQuantum Predictor - Development Tools

.PHONY: format lint test clean install migrate runserver

# Format code with black
format:
	black .

# Lint code with flake8
lint:
	flake8 .

# Run tests
test:
	python manage.py test

# Clean Python cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Install dependencies
install:
	pip install -r requirements.txt

# Run database migrations
migrate:
	python manage.py makemigrations
	python manage.py migrate

# Run development server
runserver:
	python manage.py runserver

# Full development setup
setup: install migrate
	@echo "Development environment setup complete!"

# Code quality check
quality: format lint test
	@echo "Code quality checks passed!"
