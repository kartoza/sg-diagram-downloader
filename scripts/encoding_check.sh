#!/usr/bin/env bash

# Check for UTF-8 encoding declaration in Python files
# This script is used by pre-commit hooks

for file in "$@"; do
    # Skip __init__.py files and test files
    if [[ "$file" == *"__init__.py"* ]] || [[ "$file" == *"test_"* ]]; then
        continue
    fi

    # Check if file exists and is not empty
    if [ ! -s "$file" ]; then
        continue
    fi

    # Check first two lines for encoding declaration
    head -2 "$file" | grep -q "coding[:=].*utf-8" || {
        echo "Missing UTF-8 encoding declaration in: $file"
        echo "Add '# -*- coding: utf-8 -*-' at the top of the file"
        exit 1
    }
done

exit 0
