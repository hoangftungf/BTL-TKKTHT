#!/bin/bash

# AI-Ecommerce Test Runner
# Chạy: ./scripts/run-tests.sh [service-name]

set -e

SERVICES=(
    "api-gateway"
    "auth-service"
    "user-service"
    "product-service"
    "cart-service"
    "order-service"
    "payment-service"
    "shipping-service"
    "review-service"
    "notification-service"
)

run_tests() {
    local service=$1
    echo "=========================================="
    echo "Running tests for: $service"
    echo "=========================================="

    if [ -d "services/$service" ]; then
        cd "services/$service"
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt -q
        fi
        python manage.py test --verbosity=2
        cd ../..
    else
        echo "Service not found: $service"
        return 1
    fi
}

if [ -n "$1" ]; then
    run_tests "$1"
else
    echo "Running tests for all services..."
    for service in "${SERVICES[@]}"; do
        run_tests "$service" || true
    done
fi

echo ""
echo "All tests completed!"
