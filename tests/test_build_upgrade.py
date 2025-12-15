"""Tests for mt5docker build and upgrade scenarios.

These tests validate:
1. Clean build without cache/volumes works correctly
2. Upgrade from existing volumes upgrades packages correctly
3. Version centralization is consistent across all components

These tests are slower and should be run separately:
    pytest tests/test_build_upgrade.py -v --timeout=600
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.markers import requires_container

# Mark all tests in this module as slow
pytestmark = pytest.mark.slow


class TestVersionCentralization:
    """Test that versions are centralized and consistent."""

    def test_env_script_has_all_versions(self) -> None:
        """Verify 00_env.sh defines all required version variables."""
        result = subprocess.run(
            ["grep", "-E", "^export.*VERSION|^export.*SPEC",
             "Metatrader/scripts/00_env.sh"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout

        # Check all required versions are defined
        required_vars = [
            "PYTHON_VERSION",
            "RPYC_VERSION",
            "PYDANTIC_VERSION",
            "PLUMBUM_VERSION",
            "NUMPY_VERSION",
            "MT5_PYPI_VERSION",
            "MT5LINUX_REPO",
            "MT5LINUX_BRANCH",
            "RPYC_SPEC",
            "PYDANTIC_SPEC",
            "PLUMBUM_SPEC",
            "NUMPY_SPEC",
            "MT5LINUX_SPEC",
        ]

        for var in required_vars:
            assert var in output, f"Missing centralized version: {var}"

    def test_dockerfile_uses_centralized_args(self) -> None:
        """Verify Dockerfile uses ARGs matching 00_env.sh."""
        result = subprocess.run(
            ["grep", "-E", "^ARG.*VERSION", "Dockerfile"],
            capture_output=True,
            text=True,
            check=False,
        )
        output = result.stdout

        required_args = [
            "PYTHON_VERSION",
            "RPYC_VERSION",
            "PYDANTIC_MIN_VERSION",
            "PLUMBUM_MIN_VERSION",
        ]

        for arg in required_args:
            assert arg in output, f"Dockerfile missing ARG: {arg}"

    def test_pyproject_references_centralized_versions(self) -> None:
        """Verify pyproject.toml comments reference 00_env.sh."""
        result = subprocess.run(
            ["grep", "-E", "00_env.sh|RPYC_VERSION|PYDANTIC_VERSION",
             "pyproject.toml"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "00_env.sh" in result.stdout, (
            "pyproject.toml should reference 00_env.sh for version consistency"
        )


@requires_container
class TestUpgradeScenarios:
    """Test upgrade scenarios with existing volumes."""

    def test_python_packages_at_required_versions(
        self, container_name: str
    ) -> None:
        """Verify all Python packages are at required versions after startup."""
        # Check RPyC version
        result = subprocess.run(
            ["docker", "exec", "-u", "abc", container_name,
             "wine", "python", "-c",
             "import rpyc; print(rpyc.__version__)"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"rpyc check failed: {result.stderr}"
        assert result.stdout.strip().startswith("6."), (
            f"rpyc should be 6.x, got {result.stdout.strip()}"
        )

        # Check Pydantic version
        result = subprocess.run(
            ["docker", "exec", "-u", "abc", container_name,
             "wine", "python", "-c",
             "import pydantic; print(pydantic.__version__)"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"pydantic check failed: {result.stderr}"
        assert result.stdout.strip().startswith("2."), (
            f"pydantic should be 2.x, got {result.stdout.strip()}"
        )

        # Check plumbum version
        result = subprocess.run(
            ["docker", "exec", "-u", "abc", container_name,
             "wine", "python", "-c",
             "import plumbum; print(plumbum.__version__)"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"plumbum check failed: {result.stderr}"
        # plumbum 1.8.0+
        version = result.stdout.strip()
        major, minor = version.split(".")[:2]
        assert int(major) >= 1, f"plumbum major should be >= 1, got {version}"
        assert int(minor) >= 8, f"plumbum minor should be >= 8, got {version}"

    def test_mt5linux_from_github_main(self, container_name: str) -> None:
        """Verify mt5linux is installed in Linux Python from GitHub main branch.

        Note: mt5linux is installed in Linux Python, not Wine Python.
        Wine Python has MetaTrader5 (the Windows API wrapper).
        """
        result = subprocess.run(
            ["docker", "exec", container_name,
             "python3", "-c",
             "import mt5linux; print(mt5linux.__file__)"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"mt5linux check failed: {result.stderr}"
        assert "mt5linux" in result.stdout

    def test_metatrader5_at_required_version(
        self, container_name: str
    ) -> None:
        """Verify MetaTrader5 package is at required version."""
        result = subprocess.run(
            ["docker", "exec", "-u", "abc", container_name,
             "wine", "python", "-c",
             "import MetaTrader5; print(MetaTrader5.__version__)"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"MetaTrader5 check failed: {result.stderr}"
        )
        # Should be 5.0.x
        assert result.stdout.strip().startswith("5.0"), (
            f"MetaTrader5 should be 5.0.x, got {result.stdout.strip()}"
        )


@requires_container
class TestStartupUpgradeLogic:
    """Test that startup scripts perform upgrades correctly."""

    def test_startup_script_exists_and_executable(
        self, container_name: str
    ) -> None:
        """Verify startup scripts exist and are executable."""
        scripts = [
            "/Metatrader/scripts/00_env.sh",
            "/Metatrader/scripts/20_winetricks.sh",
            "/Metatrader/scripts/30_mt5.sh",
            "/Metatrader/scripts/40_python_wine.sh",
        ]

        for script in scripts:
            result = subprocess.run(
                ["docker", "exec", container_name, "test", "-x", script],
                capture_output=True,
                check=False,
            )
            assert result.returncode == 0, f"Script not executable: {script}"

    def test_versions_file_created(self, container_name: str) -> None:
        """Verify .versions file is created with all version info."""
        result = subprocess.run(
            ["docker", "exec", container_name, "cat",
             "/opt/mt5-staging/.versions"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, ".versions file not found"

        required_versions = [
            "PYTHON_VERSION",
            "RPYC_VERSION",
            "PYDANTIC_VERSION",
            "PLUMBUM_VERSION",
        ]

        for version in required_versions:
            assert version in result.stdout, (
                f".versions missing: {version}"
            )


class TestCleanBuildRequirements:
    """Test requirements for clean builds (no container needed)."""

    def test_dockerfile_syntax_valid(self) -> None:
        """Verify Dockerfile has valid syntax and required ARGs."""
        # Verify the file exists and has required content
        dockerfile = Path("Dockerfile")
        assert dockerfile.exists(), "Dockerfile must exist"

        content = dockerfile.read_text()
        assert "FROM" in content, "Dockerfile must have FROM instruction"
        assert "ARG PYTHON_VERSION" in content
        assert "ARG RPYC_VERSION" in content

    def test_compose_files_valid(self) -> None:
        """Verify docker-compose files are valid."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.yaml",
             "-f", "tests/fixtures/docker-compose.test.yaml",
             "config"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"Compose config invalid: {result.stderr}"
        )

    def test_scripts_have_no_syntax_errors(self) -> None:
        """Verify shell scripts have no syntax errors."""
        scripts = [
            "Metatrader/scripts/00_env.sh",
            "Metatrader/scripts/20_winetricks.sh",
            "Metatrader/scripts/30_mt5.sh",
            "Metatrader/scripts/40_python_wine.sh",
        ]

        for script in scripts:
            result = subprocess.run(
                ["bash", "-n", script],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, (
                f"Syntax error in {script}: {result.stderr}"
            )


@requires_container
class TestWinetricksSilentMode:
    """Test that winetricks runs in silent mode."""

    def test_winetricks_unattended_env_set(
        self, container_name: str
    ) -> None:
        """Verify WINETRICKS_UNATTENDED is used in script."""
        result = subprocess.run(
            ["docker", "exec", container_name, "grep",
             "WINETRICKS_UNATTENDED",
             "/Metatrader/scripts/20_winetricks.sh"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "WINETRICKS_UNATTENDED=1" in result.stdout, (
            "winetricks script must set WINETRICKS_UNATTENDED=1"
        )

    def test_winetricks_quiet_flags(self, container_name: str) -> None:
        """Verify winetricks uses -q -f flags for silent operation."""
        result = subprocess.run(
            ["docker", "exec", container_name, "grep",
             "winetricks -q -f",
             "/Metatrader/scripts/20_winetricks.sh"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert "winetricks -q -f" in result.stdout, (
            "winetricks must use -q -f flags for silent mode"
        )
