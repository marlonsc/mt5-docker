"""Static validation tests - run without Docker container.

These tests validate configuration files, scripts, and build artifacts
without requiring a running container. They are fast and should pass
before any Docker operations.

Categories:
- VersionConfig: Version centralization and consistency
- DockerBuild: Dockerfile and docker-compose validation
- ScriptSyntax: Shell script syntax validation
- ConfigFiles: Configuration file validation
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

# =============================================================================
# CONSTANTS
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent

# Docker directory (all Docker-related files)
DOCKER_DIR = "docker"
CONTAINER_DIR = f"{DOCKER_DIR}/container"

# All startup scripts in execution order
STARTUP_SCRIPTS = [
    f"{CONTAINER_DIR}/Metatrader/scripts/00_env.sh",
    f"{CONTAINER_DIR}/Metatrader/scripts/05_config_unpack.sh",
    f"{CONTAINER_DIR}/Metatrader/scripts/10_prefix_init.sh",
    f"{CONTAINER_DIR}/Metatrader/scripts/20_winetricks.sh",
    f"{CONTAINER_DIR}/Metatrader/scripts/30_mt5.sh",
    f"{CONTAINER_DIR}/Metatrader/scripts/50_copy_bridge.sh",
]

# Critical scripts for container operation
CRITICAL_SCRIPTS = [
    f"{CONTAINER_DIR}/Metatrader/start.sh",
    f"{CONTAINER_DIR}/Metatrader/health_monitor.sh",
]

# All scripts combined for parametrized tests
ALL_SCRIPTS = [*STARTUP_SCRIPTS, *CRITICAL_SCRIPTS]

# Required version variables
REQUIRED_VERSIONS = [
    "PYTHON_VERSION",
    "GECKO_VERSION",
    "RPYC_VERSION",
    "PLUMBUM_VERSION",
    "NUMPY_VERSION",
]


# =============================================================================
# VERSION CONFIGURATION TESTS
# =============================================================================


class TestVersionsEnv:
    """Test versions.env - primary source of truth for versions."""

    def test_versions_env_exists(self) -> None:
        """Verify versions.env exists."""
        versions_file = PROJECT_ROOT / DOCKER_DIR / "versions.env"
        assert versions_file.exists(), "versions.env must exist as version source"

    def test_versions_env_has_all_required_versions(self) -> None:
        """Verify versions.env defines all required version variables."""
        versions_file = PROJECT_ROOT / DOCKER_DIR / "versions.env"
        content = versions_file.read_text()

        for var in REQUIRED_VERSIONS:
            assert f"{var}=" in content, f"versions.env missing: {var}"

    def test_versions_env_format_valid(self) -> None:
        """Verify versions.env uses valid KEY=VALUE format."""
        versions_file = PROJECT_ROOT / DOCKER_DIR / "versions.env"

        for raw_line in versions_file.read_text().splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            # Must be KEY=VALUE format
            assert "=" in stripped, f"Invalid format: {stripped}"
            key, value = stripped.split("=", 1)
            assert key.isupper() or key[0].isupper(), f"Key should be uppercase: {key}"
            assert value, f"Empty value for: {key}"

    def test_python_version_is_312(self) -> None:
        """Verify Python version is 3.12.x (numpy compatibility)."""
        versions_file = PROJECT_ROOT / DOCKER_DIR / "versions.env"
        content = versions_file.read_text()

        match = re.search(r"PYTHON_VERSION=(\S+)", content)
        assert match, "PYTHON_VERSION not found"
        version = match.group(1)
        assert version.startswith("3.12"), f"Python must be 3.12.x, got {version}"

    def test_numpy_version_is_126x(self) -> None:
        """Verify numpy version is 1.26.x (Wine compatibility)."""
        versions_file = PROJECT_ROOT / DOCKER_DIR / "versions.env"
        content = versions_file.read_text()

        match = re.search(r"NUMPY_VERSION=(\S+)", content)
        assert match, "NUMPY_VERSION not found"
        version = match.group(1)
        assert version.startswith(
            "1.26"
        ), f"NumPy must be 1.26.x for Wine, got {version}"

    def test_rpyc_version_is_6x(self) -> None:
        """Verify RPyC version is 6.x."""
        versions_file = PROJECT_ROOT / DOCKER_DIR / "versions.env"
        content = versions_file.read_text()

        match = re.search(r"RPYC_VERSION=(\S+)", content)
        assert match, "RPYC_VERSION not found"
        version = match.group(1)
        assert version.startswith("6."), f"RPyC must be 6.x, got {version}"


class TestVersionConsistency:
    """Test version consistency across all configuration files."""

    def test_dockerfile_args_match_versions_env(self) -> None:
        """Verify Dockerfile ARG defaults match versions.env."""
        versions = self._load_versions_env()
        dockerfile = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()

        version_vars = [
            "PYTHON_VERSION",
            "RPYC_VERSION",
            "PLUMBUM_VERSION",
            "NUMPY_VERSION",
        ]
        for var in version_vars:
            expected = versions.get(var)
            # Match ARG VAR=value pattern
            pattern = rf"ARG {var}=(\S+)"
            match = re.search(pattern, dockerfile)
            assert match, f"Dockerfile missing ARG {var}"
            actual = match.group(1)
            assert (
                actual == expected
            ), f"{var}: Dockerfile={actual}, versions.env={expected}"

    def test_pyproject_references_versions_env(self) -> None:
        """Verify pyproject.toml comments reference versions.env."""
        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text()
        assert (
            "versions.env" in pyproject
        ), "pyproject.toml should reference versions.env"

    def test_env_script_uses_versions_env(self) -> None:
        """Verify 00_env.sh sources or references versions.env."""
        script_path = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/scripts/00_env.sh"
        env_script = script_path.read_text()
        # Should either source versions.env or have fallback values
        assert "PYTHON_VERSION" in env_script, "00_env.sh must handle PYTHON_VERSION"
        assert "RPYC_VERSION" in env_script, "00_env.sh must handle RPYC_VERSION"

    def _load_versions_env(self) -> dict[str, str]:
        """Load versions from versions.env file."""
        versions: dict[str, str] = {}
        versions_file = PROJECT_ROOT / DOCKER_DIR / "versions.env"

        for raw_line in versions_file.read_text().splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                key, value = stripped.split("=", 1)
                versions[key] = value

        return versions


# =============================================================================
# DOCKERFILE TESTS
# =============================================================================


class TestDockerfile:
    """Test Dockerfile structure and configuration."""

    def test_dockerfile_exists(self) -> None:
        """Verify Dockerfile exists."""
        dockerfile = PROJECT_ROOT / DOCKER_DIR / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile must exist"

    def test_dockerfile_has_buildkit_syntax(self) -> None:
        """Verify Dockerfile uses BuildKit syntax."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()
        assert "syntax=docker/dockerfile" in content, "Should use BuildKit syntax"

    def test_dockerfile_has_multistage_build(self) -> None:
        """Verify Dockerfile uses multi-stage build."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()

        required_stages = ["base", "wine-base", "downloader", "wine-builder", "runtime"]
        for stage in required_stages:
            assert f"AS {stage}" in content, f"Missing stage: {stage}"

    def test_dockerfile_has_required_args(self) -> None:
        """Verify Dockerfile has all required ARGs."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()

        for arg in [*REQUIRED_VERSIONS, "BUILD_DATE", "VERSION"]:
            assert f"ARG {arg}" in content, f"Dockerfile missing ARG: {arg}"

    def test_dockerfile_exposes_required_ports(self) -> None:
        """Verify Dockerfile exposes required ports."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()

        assert "EXPOSE" in content
        assert "3000" in content, "Must expose VNC port 3000"
        assert "8001" in content, "Must expose RPyC port 8001"

    def test_dockerfile_has_volume_config(self) -> None:
        """Verify Dockerfile declares /config volume."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()
        assert "VOLUME /config" in content, "Must declare /config volume"

    def test_dockerfile_has_oci_labels(self) -> None:
        """Verify Dockerfile has OCI-compliant labels."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()

        required_labels = [
            "org.opencontainers.image.title",
            "org.opencontainers.image.description",
            "org.opencontainers.image.version",
            "org.opencontainers.image.source",
        ]
        for label in required_labels:
            assert label in content, f"Missing OCI label: {label}"

    def test_dockerfile_copies_scripts(self) -> None:
        """Verify Dockerfile copies Metatrader scripts."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()
        assert "COPY container/Metatrader" in content, "Must copy Metatrader scripts"

    def test_dockerfile_copies_s6_services(self) -> None:
        """Verify Dockerfile copies s6-overlay services."""
        content = (PROJECT_ROOT / DOCKER_DIR / "Dockerfile").read_text()
        assert "s6-overlay" in content, "Must copy s6-overlay services"


# =============================================================================
# DOCKER COMPOSE TESTS
# =============================================================================


class TestDockerCompose:
    """Test docker-compose.yaml configuration."""

    def test_compose_file_exists(self) -> None:
        """Verify compose.yaml exists."""
        compose = PROJECT_ROOT / DOCKER_DIR / "compose.yaml"
        assert compose.exists(), "docker/compose.yaml must exist"

    def test_compose_config_valid(self) -> None:
        """Verify compose.yaml has valid syntax."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker/compose.yaml", "config", "--quiet"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Compose config invalid: {result.stderr}"

    def test_compose_has_env_file_required(self) -> None:
        """Verify compose requires .env file."""
        content = (PROJECT_ROOT / DOCKER_DIR / "compose.yaml").read_text()
        assert "env_file:" in content
        assert "required: true" in content, ".env should be required"

    def test_compose_has_healthcheck(self) -> None:
        """Verify compose defines healthcheck."""
        content = (PROJECT_ROOT / DOCKER_DIR / "compose.yaml").read_text()
        assert "healthcheck:" in content
        assert "test:" in content
        assert "interval:" in content
        assert "start_period:" in content

    def test_compose_has_resource_limits(self) -> None:
        """Verify compose defines resource limits."""
        content = (PROJECT_ROOT / DOCKER_DIR / "compose.yaml").read_text()
        assert "deploy:" in content
        assert "resources:" in content
        assert "limits:" in content
        assert "memory:" in content

    def test_compose_has_security_options(self) -> None:
        """Verify compose has required security options for MT5."""
        content = (PROJECT_ROOT / DOCKER_DIR / "compose.yaml").read_text()
        assert "cap_add:" in content
        assert "SYS_PTRACE" in content, "MT5 requires SYS_PTRACE capability"
        assert "security_opt:" in content
        assert "seccomp:unconfined" in content, "MT5 requires seccomp:unconfined"

    def test_compose_has_restart_policy(self) -> None:
        """Verify compose has restart policy."""
        content = (PROJECT_ROOT / DOCKER_DIR / "compose.yaml").read_text()
        assert "restart:" in content
        assert "unless-stopped" in content

    def test_compose_has_ulimits(self) -> None:
        """Verify compose sets file descriptor limits."""
        content = (PROJECT_ROOT / DOCKER_DIR / "compose.yaml").read_text()
        assert "ulimits:" in content
        assert "nofile:" in content

    def test_compose_uses_env_variables_for_ports(self) -> None:
        """Verify compose uses environment variables for port configuration."""
        content = (PROJECT_ROOT / DOCKER_DIR / "compose.yaml").read_text()
        assert "${MT5_VNC_PORT:-" in content, "VNC port should use env var"
        assert "${MT5_RPYC_PORT:-" in content, "RPyC port should use env var"
        assert "${MT5_CONTAINER_NAME:-" in content, "Container name should use env var"


# =============================================================================
# SHELL SCRIPT TESTS
# =============================================================================


class TestShellScriptSyntax:
    """Test shell script syntax validation."""

    @pytest.mark.parametrize("script", ALL_SCRIPTS)
    def test_script_exists(self, script: str) -> None:
        """Verify script file exists."""
        script_path = PROJECT_ROOT / script
        assert script_path.exists(), f"Script not found: {script}"

    @pytest.mark.parametrize("script", ALL_SCRIPTS)
    def test_script_syntax_valid(self, script: str) -> None:
        """Verify script has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", script],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, f"Syntax error in {script}: {result.stderr}"

    @pytest.mark.parametrize("script", ALL_SCRIPTS)
    def test_script_is_executable(self, script: str) -> None:
        """Verify script has executable permission."""
        script_path = PROJECT_ROOT / script
        assert script_path.stat().st_mode & 0o111, f"Script not executable: {script}"

    @pytest.mark.parametrize("script", ALL_SCRIPTS)
    def test_script_has_shebang(self, script: str) -> None:
        """Verify script has proper shebang."""
        script_path = PROJECT_ROOT / script
        first_line = script_path.read_text().splitlines()[0]
        assert first_line.startswith("#!"), f"Missing shebang in {script}"
        valid_shebang = "bash" in first_line or "sh" in first_line
        assert valid_shebang, f"Invalid shebang: {first_line}"


class TestStartupScriptContent:
    """Test startup script specific content."""

    def test_env_script_exports_versions(self) -> None:
        """Verify 00_env.sh exports version variables."""
        script_path = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/scripts/00_env.sh"
        content = script_path.read_text()

        for var in ["PYTHON_VERSION", "RPYC_VERSION", "PLUMBUM_VERSION"]:
            assert var in content, f"00_env.sh must handle {var}"

    def test_winetricks_script_is_unattended(self) -> None:
        """Verify 20_winetricks.sh uses unattended mode."""
        scripts_dir = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/scripts"
        content = (scripts_dir / "20_winetricks.sh").read_text()
        assert "WINETRICKS_UNATTENDED=1" in content, "Must set WINETRICKS_UNATTENDED=1"
        assert "winetricks -q" in content, "Must use -q flag for silent mode"

    def test_mt5_script_handles_installation(self) -> None:
        """Verify 30_mt5.sh handles MT5 installation."""
        script_path = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/scripts/30_mt5.sh"
        content = script_path.read_text()
        assert "mt5setup.exe" in content or "MetaTrader" in content
        assert "wine" in content.lower(), "Must use wine for MT5"

    def test_copy_bridge_script(self) -> None:
        """Verify 50_copy_bridge.sh copies bridge.py to Wine."""
        scripts_dir = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/scripts"
        content = (scripts_dir / "50_copy_bridge.sh").read_text()
        assert "bridge.py" in content, "Must copy bridge.py"
        assert "BRIDGE_SOURCE" in content, "Must define bridge source path"

    def test_start_script_runs_scripts_in_order(self) -> None:
        """Verify start.sh runs initialization scripts."""
        content = (PROJECT_ROOT / CONTAINER_DIR / "Metatrader/start.sh").read_text()
        # Should reference scripts directory
        assert "scripts" in content or "00_env" in content

    def test_health_monitor_checks_rpyc(self) -> None:
        """Verify health_monitor.sh checks RPyC service."""
        script_path = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/health_monitor.sh"
        content = script_path.read_text()
        # Should check port 8001 or rpyc
        assert "8001" in content or "rpyc" in content.lower()


# =============================================================================
# S6-OVERLAY SERVICE TESTS
# =============================================================================


class TestS6Services:
    """Test s6-overlay service configuration."""

    def test_s6_service_directory_exists(self) -> None:
        """Verify s6 service directory exists."""
        s6_dir = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/etc/s6-overlay"
        assert s6_dir.exists(), "s6-overlay directory must exist"

    def test_s6_mt5server_service_exists(self) -> None:
        """Verify svc-mt5server service is defined."""
        s6_base = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/etc/s6-overlay/s6-rc.d"
        service_dir = s6_base / "svc-mt5server"
        assert service_dir.exists(), "svc-mt5server service must exist"

    def test_s6_service_has_run_script(self) -> None:
        """Verify service has run script."""
        s6_base = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/etc/s6-overlay/s6-rc.d"
        run_script = s6_base / "svc-mt5server/run"
        assert run_script.exists(), "Service must have run script"

    def test_s6_service_has_finish_script(self) -> None:
        """Verify service has finish script."""
        s6_base = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/etc/s6-overlay/s6-rc.d"
        finish_script = s6_base / "svc-mt5server/finish"
        assert finish_script.exists(), "Service should have finish script"


# =============================================================================
# CONFIGURATION FILE TESTS
# =============================================================================


class TestConfigFiles:
    """Test configuration files."""

    def test_env_example_exists(self) -> None:
        """Verify .env.example exists for documentation."""
        env_example = PROJECT_ROOT / "config" / ".env.example"
        assert env_example.exists(), ".env.example should exist for documentation"

    def test_env_example_has_required_vars(self) -> None:
        """Verify .env.example documents required variables."""
        env_example = PROJECT_ROOT / "config" / ".env.example"
        content = env_example.read_text()

        required_vars = ["MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"]
        for var in required_vars:
            assert var in content, f".env.example missing: {var}"

    def test_dockerignore_exists(self) -> None:
        """Verify .dockerignore exists."""
        dockerignore = PROJECT_ROOT / DOCKER_DIR / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore should exist"

    def test_dockerignore_excludes_sensitive(self) -> None:
        """Verify .dockerignore excludes sensitive files."""
        content = (PROJECT_ROOT / DOCKER_DIR / ".dockerignore").read_text()

        # Should exclude .env, .git, etc.
        should_exclude = [".env", ".git"]
        for item in should_exclude:
            assert item in content, f".dockerignore should exclude: {item}"

    def test_pyproject_toml_exists(self) -> None:
        """Verify pyproject.toml exists."""
        pyproject = PROJECT_ROOT / "pyproject.toml"
        assert pyproject.exists(), "pyproject.toml must exist"

    def test_pyproject_has_pytest_config(self) -> None:
        """Verify pyproject.toml has pytest configuration."""
        content = (PROJECT_ROOT / "pyproject.toml").read_text()
        assert "[tool.pytest" in content, "Must have pytest configuration"
        assert "testpaths" in content


# =============================================================================
# DIRECTORY STRUCTURE TESTS
# =============================================================================


class TestDirectoryStructure:
    """Test project directory structure."""

    def test_metatrader_directory_exists(self) -> None:
        """Verify Metatrader directory exists."""
        assert (PROJECT_ROOT / CONTAINER_DIR / "Metatrader").is_dir()

    def test_scripts_directory_exists(self) -> None:
        """Verify scripts directory exists."""
        assert (PROJECT_ROOT / CONTAINER_DIR / "Metatrader/scripts").is_dir()

    def test_bridge_py_exists(self) -> None:
        """Verify bridge.py (RPyC server) exists."""
        bridge_path = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/bridge.py"
        assert bridge_path.exists(), "bridge.py must exist for RPyC server"

    def test_bridge_py_is_standalone(self) -> None:
        """Verify bridge.py has no mt5linux dependencies."""
        bridge_path = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/bridge.py"
        content = bridge_path.read_text()
        # Should only import rpyc and stdlib
        assert "import rpyc" in content, "Must import rpyc"
        assert "from mt5linux" not in content, "Must not depend on mt5linux modules"
        assert "import structlog" not in content, "Must not depend on structlog"

    def test_root_directory_exists(self) -> None:
        """Verify root directory (LinuxServer defaults) exists."""
        assert (PROJECT_ROOT / CONTAINER_DIR / "root").is_dir()

    def test_tests_directory_exists(self) -> None:
        """Verify tests directory exists."""
        assert (PROJECT_ROOT / "tests").is_dir()

    def test_startup_scripts_numbered_correctly(self) -> None:
        """Verify startup scripts follow numbered naming convention."""
        scripts_dir = PROJECT_ROOT / CONTAINER_DIR / "Metatrader/scripts"
        scripts = sorted(scripts_dir.glob("*.sh"))

        # Should have numbered prefixes: 00, 05, 10, 20, 30, 50
        expected_prefixes = ["00", "05", "10", "20", "30", "50"]

        for script in scripts:
            prefix = script.name[:2]
            if prefix.isdigit():
                assert (
                    prefix in expected_prefixes
                ), f"Unexpected script prefix: {script.name}"
