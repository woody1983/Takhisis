#!/bin/bash
# Run tests with coverage report

echo "Running tests..."
python -m pytest test_app.py -v "$@"

echo ""
echo "Running tests with coverage..."
python -m pytest test_app.py --cov=app --cov-report=term-missing
