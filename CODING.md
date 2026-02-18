# Coding Standards

This document outlines the coding standards for the SG Diagram Downloader project.

## Python Style Guide

### Formatting

- **Line length**: 120 characters maximum
- **Formatter**: Black (automatically enforced via pre-commit)
- **Import sorting**: isort with Black-compatible profile

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Keep functions focused and small
- Prefer explicit over implicit

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def download_diagram(parcel_id: str, output_path: str) -> bool:
    """Download a diagram for the specified parcel.

    Args:
        parcel_id: The unique identifier of the parcel.
        output_path: The file path where the diagram will be saved.

    Returns:
        True if download was successful, False otherwise.

    Raises:
        SGDownloadError: If the download fails due to network issues.
    """
    pass
```

### Type Hints

Use type hints for function signatures:

```python
from typing import Optional, List, Dict

def process_parcels(parcel_ids: List[str]) -> Dict[str, bool]:
    """Process multiple parcels."""
    pass
```

## File Organization

### Encoding

All Python files should have a UTF-8 encoding declaration:

```python
# -*- coding: utf-8 -*-
```

### Imports

Order imports as follows:
1. Standard library imports
2. Third-party imports
3. Local application imports

```python
# -*- coding: utf-8 -*-
import os
import sys
from typing import Optional

from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QMessageBox

from .sg_utilities import get_parcel_id
from .database_manager import DatabaseManager
```

## Error Handling

- Use specific exception types where possible
- Document exceptions in docstrings
- Log errors appropriately

```python
try:
    result = download_file(url)
except NetworkError as e:
    logger.error(f"Network error downloading {url}: {e}")
    raise SGDownloadError(f"Failed to download: {e}") from e
```

## Testing

- Write tests for new functionality
- Use pytest fixtures for common setup
- Mark tests appropriately (unit, integration, slow)

```python
import pytest

@pytest.mark.unit
def test_parcel_id_validation():
    """Test that parcel ID validation works correctly."""
    assert is_valid_parcel_id("ABC123") is True
    assert is_valid_parcel_id("") is False
```

## Git Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Keep first line under 72 characters
- Reference issues when applicable

```
Add download retry mechanism

Implements automatic retry with exponential backoff for failed
diagram downloads. Retries up to 3 times before giving up.

Fixes #42
```

## Security

- Never commit secrets or API keys
- Validate all external input
- Use parameterized queries for database operations
- Run bandit security checks before committing
