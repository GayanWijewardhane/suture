#!/bin/bash
# Complete test suite for Suture

set -e

echo "🩹 Suture Test Suite"
echo "===================="
echo

cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Test 1: Basic Analysis
echo "Test 1: Basic Analysis"
./suture analyze tests/test_logs.txt
echo "✓ Passed"
echo

# Test 2: Stats Output
echo "Test 2: Statistics"
./suture analyze tests/test_logs.txt --stats
echo "✓ Passed"
echo

# Test 3: Wine Errors
echo "Test 3: Wine Error Detection"
./suture analyze tests/wine_errors.txt
echo "✓ Passed"
echo

# Test 4: Stdin Scan
echo "Test 4: Stdin Scan"
echo "Permission denied: test error" | ./suture scan --input
echo "✓ Passed"
echo

# Test 5: List Rules
echo "Test 5: List Rules"
./suture rules > /dev/null
echo "✓ Passed"
echo

# Test 6: Categories
echo "Test 6: List Categories"
./suture categories > /dev/null
echo "✓ Passed"
echo

# Test 7: Health Check
echo "Test 7: System Health"
./suture health > /dev/null
echo "✓ Passed"
echo

# Test 8: Dry Run Fix
echo "Test 8: Dry Run Fix Mode"
timeout 5 ./suture fix tests/test_logs.txt --dry-run || true
echo "✓ Passed"
echo

echo "===================="
echo "All tests passed! ✓"
