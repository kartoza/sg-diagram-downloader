#!/usr/bin/env bash
echo "Running QGIS with the SGDiagramDownloader profile:"
echo "--------------------------------"
echo "Do you want to enable debug mode?"
choice=$(gum choose "Yes" "No")
case $choice in
    "Yes")
        developer_mode=1
        sentry_disabled=1
        ;;
    "No")
        developer_mode=0
        sentry_disabled=0
        ;;
esac

# Running on local used to skip tests that will not work in a local dev env
SG_DOWNLOADER_LOG=$HOME/SGDiagramDownloader.log
SG_DOWNLOADER_TEST_DIR="$(pwd)/test" # Set test directory relative to project root
rm -f "$SG_DOWNLOADER_LOG"

# Using Ivan Mincis nix spatial project and a flake
# see flake.nix for implementation details
SG_DOWNLOADER_LOG=${SG_DOWNLOADER_LOG} \
    SG_DOWNLOADER_DEBUG=${developer_mode} \
    SG_DOWNLOADER_SENTRY_DISABLED=${sentry_disabled} \
    SG_DOWNLOADER_TEST_DIR=${SG_DOWNLOADER_TEST_DIR} \
    RUNNING_ON_LOCAL=1 \
    nix run .#default -- --profile SGDiagramDownloader
