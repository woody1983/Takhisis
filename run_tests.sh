#!/bin/bash
# Run tests with coverage report

echo "Running tests..."
./venv/bin/python3 -m pytest test_app.py -v "$@"

echo ""
echo "Running tests with coverage..."
./venv/bin/python3 -m pytest test_app.py --cov=app --cov-report=term-missing
