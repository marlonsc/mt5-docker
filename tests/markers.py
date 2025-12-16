"""Pytest markers for mt5docker tests.

This module defines pytest markers that can be imported by test files
without pulling in conftest.py dependencies.
"""

from __future__ import annotations

import pytest

# Pytest marker for tests requiring container
requires_container = pytest.mark.usefixtures("docker_container")
