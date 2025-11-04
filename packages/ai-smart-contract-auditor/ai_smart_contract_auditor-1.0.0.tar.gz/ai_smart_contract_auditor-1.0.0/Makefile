# Makefile for AI Smart Contract Auditor
# Common commands for testing, development, and deployment

.PHONY: help test test-unit test-integration test-e2e test-performance test-all test-parallel coverage lint format clean install

# Default target
help:
	@echo "AI Smart Contract Auditor - Development Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test              - Run all tests (except performance)"
	@echo "  make test-parallel     - Run all tests in parallel (2x faster)"
	@echo "  make test-unit         - Run unit tests only"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-e2e          - Run end-to-end tests only"
	@echo "  make test-performance  - Run performance benchmarks"
	@echo "  make test-all          - Run all tests including performance"
	@echo "  make test-fast         - Run fast tests only"
	@echo "  make test-watch        - Run tests in watch mode"
	@echo ""
	@echo "Coverage:"
	@echo "  make coverage          - Run tests with coverage report"
	@echo "  make coverage-html     - Generate HTML coverage report"
	@echo "  make coverage-report   - Open HTML coverage report in browser"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint              - Run linters (pylint, flake8)"
	@echo "  make format            - Format code (black, isort)"
	@echo "  make type-check        - Run type checking (mypy)"
	@echo "  make quality           - Run all quality checks"
	@echo ""
	@echo "Development:"
	@echo "  make install           - Install dependencies"
	@echo "  make install-dev       - Install dev dependencies"
	@echo "  make clean             - Clean build artifacts"
	@echo "  make audit             - Run audit on test contract"
	@echo ""
	@echo "CI/CD:"
	@echo "  make ci                - Run CI pipeline locally"
	@echo "  make pre-commit        - Install pre-commit hooks"

# Testing targets
test:
	pytest tests/ -v -m "not performance"

test-parallel:
	pytest tests/ -n auto -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

test-performance:
	pytest tests/performance/ -v -m performance --benchmark-only

test-all:
	pytest tests/ -v

test-fast:
	pytest tests/ -v -m "not slow and not performance"

test-watch:
	pytest-watch tests/ -v

# Coverage targets
coverage:
	pytest tests/ --cov=src --cov-report=term-missing -m "not performance"

coverage-html:
	pytest tests/ --cov=src --cov-report=html -m "not performance"
	@echo "Coverage report generated in htmlcov/index.html"

coverage-report: coverage-html
	python -m webbrowser htmlcov/index.html

# Code quality targets
lint:
	@echo "Running pylint..."
	pylint src/ --exit-zero || true
	@echo "Running flake8..."
	flake8 src/ tests/ --max-line-length=100 --ignore=E203,W503 || true

format:
	@echo "Running black..."
	black src/ tests/
	@echo "Running isort..."
	isort src/ tests/ --profile black

type-check:
	@echo "Running mypy..."
	mypy src/ --ignore-missing-imports || true

quality: lint type-check
	@echo "Quality checks complete"

# Development targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-mock pytest-benchmark pytest-watch
	pip install pylint black isort mypy flake8
	pip install pre-commit

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .mypy_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Clean complete"

audit:
	python ai_auditor.py examples/vulnerable/reentrancy.sol

# CI/CD targets
ci: clean install-dev test-all lint type-check
	@echo "CI pipeline complete"

pre-commit:
	pip install pre-commit
	pre-commit install
	@echo "Pre-commit hooks installed"

# Utility targets
.PHONY: version
version:
	@python -c "print('AI Smart Contract Auditor v2.0.0')"

.PHONY: info
info:
	@echo "Python: $(shell python --version)"
	@echo "Pytest: $(shell pytest --version)"
	@echo "Tests: $(shell pytest --collect-only -q 2>&1 | tail -1)"


# Mutation Testing
.PHONY: mutate mutate-run mutate-results mutate-html

mutate: ## Run mutation testing (full suite)
	@echo "Running mutation testing..."
	@mutmut run --paths-to-mutate=src/

mutate-run: ## Run mutation testing on specific module
	@echo "Running mutation testing on $(MODULE)..."
	@mutmut run --paths-to-mutate=src/$(MODULE)

mutate-results: ## Show mutation testing results
	@mutmut results

mutate-html: ## Generate HTML mutation report
	@mutmut html
	@echo "Mutation report generated at html/index.html"

# Test Quality Tracking
.PHONY: track-quality quality-report quality-trends

track-quality:  ## Track test quality metrics
	@echo "Tracking test quality metrics..."
	@python scripts/track_test_quality.py

quality-report:  ## Generate comprehensive quality report
	@echo "Generating quality report..."
	@pytest tests/ --cov=src --cov-report=term --cov-report=html -v
	@echo "\nCoverage report: htmlcov/index.html"

quality-trends:  ## Show quality trends over time
	@echo "Test Quality Trends:"
	@echo "===================="
	@if [ -d .metrics ]; then \
		python -c "import json; import glob; \
		files = sorted(glob.glob('.metrics/quality-*.json')); \
		print('Date       | Coverage | Tests | Mutation'); \
		print('-----------|----------|-------|----------'); \
		for f in files[-10:]: \
			data = json.load(open(f)); \
			date = data['date'][:10]; \
			cov = data.get('coverage', 0); \
			tests = data.get('tests', {}).get('total', 0); \
			mut = data.get('mutation', {}).get('score', 0); \
			print(f'{date} | {cov:6.2f}% | {tests:5d} | {mut:6.2f}%')"; \
	else \
		echo "No metrics found. Run 'make track-quality' first."; \
	fi


# ============================================================================
# Mutation Testing (cosmic-ray)
# ============================================================================

.PHONY: mutate-cosmic mutate-quick mutate-report-cosmic

mutate-cosmic:  ## Run cosmic-ray mutation testing
	@echo "Running cosmic-ray mutation testing..."
	cosmic-ray init cosmic-ray.toml session.sqlite
	cosmic-ray exec session.sqlite
	@echo "Mutation testing complete. View results with: make mutate-report-cosmic"

mutate-quick:  ## Run quick mutation testing with mutatest
	@echo "Running quick mutation testing with mutatest..."
	mutatest -s src/features/ -t "pytest tests/unit/features/" -n 100

mutate-report-cosmic:  ## Generate cosmic-ray mutation report
	@echo "Generating cosmic-ray mutation report..."
	cosmic-ray dump session.sqlite | python3 -m json.tool > mutation-results.json
	@echo "JSON report: mutation-results.json"
	@if command -v cr-html > /dev/null; then \
		cr-html session.sqlite > htmlcov/mutation-report.html; \
		echo "HTML report: htmlcov/mutation-report.html"; \
	else \
		echo "Install cr-html for HTML reports: pip install cr-html"; \
	fi
