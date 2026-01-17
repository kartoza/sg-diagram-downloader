#!/usr/bin/env bash

# Cleanup development folder
#
RESET='\033[0m'
ORANGE='\033[38;2;237;177;72m'
# Clear screen and show welcome banner
clear
echo -e "$RESET$ORANGE"
if [ -f "resources/icon.png" ]; then
    chafa resources/icon.png --size=20x40 --colors=256 | sed 's/^/                  /'
fi
# Quick tips with icons
echo -e "$RESET$ORANGE \n__________________________________________________________________\n"
echo "Removing pycaches, .venv etc ..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".venv" -exec rm -rf {} +
echo "Removing core dumps and other unneeded files ..."
find . -type f -name "core.*" -exec rm -f {} +
find . -type f -name "*.log" -exec rm -f {} +
find . -type f -name "*.tmp" -exec rm -f {} +
echo "Removing build artifacts ..."
rm -rf build/ dist/
echo -e "$RESET$ORANGE \n__________________________________________________________________\n"
