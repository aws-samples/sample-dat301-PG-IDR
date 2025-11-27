#!/bin/bash
# Wrapper script for stress test with venv activation

# Activate virtual environment
if [ -f /workshop/mahavat_agent/venv/bin/activate ]; then
    source /workshop/mahavat_agent/venv/bin/activate
fi

# Run stress test with absolute path
python3 /workshop/load-test/stress_test.py "$@"
