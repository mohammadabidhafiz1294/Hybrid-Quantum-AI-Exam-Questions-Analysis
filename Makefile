# VQE Exam Topic Prediction System - Development Tools

.PHONY: format lint test clean install devserver

# Format code with black
format:
	black src/ tests/

# Lint code with flake8
lint:
	flake8 src/ tests/

# Run tests
test:
	PYTHONPATH=. pytest tests/ -v

# Clean Python cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Install dependencies
install:
	pip install -r requirements.txt

# Run development server
devserver:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Full development setup
setup: install
	@echo "Development environment setup complete!"

# Code quality check
quality: format lint test
	@echo "Code quality checks passed!"

# Run with virtual environment
run:
	source hybrid-venv/bin/activate && $(MAKE) $(filter-out run,$(MAKECMDGOALS))

# Help
help:
	@echo "Available commands:"
	@echo "  format     - Format code with black"
	@echo "  lint       - Lint code with flake8"
	@echo "  test       - Run tests with pytest"
	@echo "  clean      - Clean Python cache files"
	@echo "  install    - Install dependencies"
	@echo "  devserver  - Run development server"
	@echo "  setup      - Full development setup"
	@echo "  quality    - Run all code quality checks"
	@echo "  run        - Run commands with virtual environment"
