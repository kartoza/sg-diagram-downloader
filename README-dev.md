# SG Diagram Downloader - Developer Guide

This document provides instructions for setting up a development environment for the SG Diagram Downloader QGIS plugin.

## Prerequisites

- [Nix package manager](https://nixos.org/download.html) with flakes enabled
- [direnv](https://direnv.net/) (recommended)
- Git

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/kartoza/sg-diagram-downloader.git
cd sg-diagram-downloader
```

### 2. Enable direnv (Recommended)

If you have direnv installed:

```bash
direnv allow
```

This will automatically set up the development environment when you enter the directory.

### 3. Manual Environment Setup

If you're not using direnv:

```bash
nix develop
```

## Development Commands

### Running QGIS

Launch QGIS with the plugin profile:

```bash
./scripts/start_qgis.sh        # Latest stable QGIS
./scripts/start_qgis_ltr.sh    # QGIS LTR version
./scripts/start_qgis_master.sh # QGIS master/dev version
```

### Pre-commit Checks

Run all pre-commit hooks:

```bash
./scripts/checks.sh
```

Or manually:

```bash
pre-commit run --all-files
```

### Cleanup

Remove build artifacts, caches, and temporary files:

```bash
./scripts/clean.sh
```

### Plugin Management

Using the admin.py script:

```bash
# Build the plugin
python admin.py build

# Install to QGIS plugins directory
python admin.py install

# Uninstall from QGIS
python admin.py uninstall

# Create a distribution zip
python admin.py generate-zip

# Generate plugin repository XML
python admin.py generate-plugin-repo-xml
```

## Project Structure

```
sg-diagram-downloader/
├── .github/workflows/    # GitHub Actions CI/CD
├── data/                 # Plugin data files (sqlite, gpkg)
├── resources/            # Icons and other resources
├── scripts/              # Development helper scripts
├── test/                 # Test files and test data
├── admin.py              # Plugin admin automation
├── flake.nix             # Nix flake for dev environment
├── pyproject.toml        # Python tool configuration
├── pytest.ini            # Pytest configuration
├── metadata.txt          # QGIS plugin metadata
└── *.py                  # Plugin source files
```

## Testing

Run tests with pytest:

```bash
pytest
```

Run specific test markers:

```bash
pytest -m unit          # Only unit tests
pytest -m integration   # Only integration tests
pytest -m "not slow"    # Skip slow tests
```

## Code Quality

The project uses several tools for code quality:

- **Black**: Code formatting (line length: 120)
- **isort**: Import sorting
- **flake8**: Linting
- **bandit**: Security scanning
- **shellcheck**: Shell script linting

All checks are run automatically via pre-commit hooks.

## GitHub Actions

- **CI**: Runs on push/PR to main/develop, tests against multiple QGIS versions
- **Release**: Triggered on version tags (v*), creates GitHub releases and updates plugin repository

## Creating a Release

1. Update version in `metadata.txt`
2. Commit changes
3. Create and push a version tag:

```bash
git tag v3.3
git push origin v3.3
```

The release workflow will automatically:
- Create a GitHub release
- Build and attach the plugin zip
- Update the plugin repository XML

## Nix Flake

Available packages and apps:

```bash
nix flake show           # Show all available outputs
nix run .#qgis           # Run stable QGIS
nix run .#qgis-ltr       # Run QGIS LTR
nix run .#qgis-master    # Run QGIS master
```
