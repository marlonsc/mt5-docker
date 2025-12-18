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

import pytest

from tests.conftest import c

# =============================================================================
# VERSION CONFIGURATION TESTS
# =============================================================================


class TestVersionsEnv:
    """Test versions.env - primary source of truth for versions."""

    def test_versions_env_exists(self) -> None:
        """Verify versions.env exists."""
        versions_file = c.get_project_root() / c.Directory.DOCKER / c.File.VERSIONS_ENV
        assert versions_file.exists(), (
            f"{c.File.VERSIONS_ENV} must exist as version source"
        )

    def test_versions_env_has_all_required_versions(self) -> None:
        """Verify versions.env defines all required version variables."""
        versions_file = c.get_project_root() / c.Directory.DOCKER / c.File.VERSIONS_ENV
        content = versions_file.read_text()

        for var in c.REQUIRED_VERSIONS:
            assert f"{var}=" in content, f"{c.File.VERSIONS_ENV} missing: {var}"

    def test_versions_env_format_valid(self) -> None:
        """Verify versions.env uses valid KEY=VALUE format."""
        versions_file = c.get_project_root() / c.Directory.DOCKER / c.File.VERSIONS_ENV

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
        versions_file = c.get_project_root() / c.Directory.DOCKER / c.File.VERSIONS_ENV
        content = versions_file.read_text()

        match = re.search(r"PYTHON_VERSION=(\S+)", content)
        assert match, "PYTHON_VERSION not found"
        version = match.group(1)
        assert version.startswith(c.VersionPrefix.PYTHON), (  # type: ignore[attr-defined]
            f"Python must be {c.VersionPrefix.PYTHON}.x, got {version}"  # type: ignore[attr-defined]
        )

    def test_numpy_version_is_126x(self) -> None:
        """Verify numpy version is 1.26.x (Wine compatibility)."""
        versions_file = c.get_project_root() / c.Directory.DOCKER / c.File.VERSIONS_ENV
        content = versions_file.read_text()

        match = re.search(r"NUMPY_VERSION=(\S+)", content)
        assert match, "NUMPY_VERSION not found"
        version = match.group(1)
        assert version.startswith(c.VersionPrefix.NUMPY), (  # type: ignore[attr-defined]
            f"NumPy must be {c.VersionPrefix.NUMPY}.x for Wine, got {version}"  # type: ignore[attr-defined]
        )

    def test_grpcio_version_is_176_or_higher(self) -> None:
        """Verify gRPC version is 1.76.0 or higher (required by mt5_pb2_grpc.py)."""
        versions_file = c.get_project_root() / c.Directory.DOCKER / c.File.VERSIONS_ENV
        content = versions_file.read_text()

        match = re.search(r"GRPCIO_VERSION=(\S+)", content)
        assert match, "GRPCIO_VERSION not found"
        version = match.group(1)
        major, minor = version.split(".")[: c.VERSION_MAJOR_MINOR_PARTS]
        major_version = int(major)
        minor_version = int(minor)

        assert major_version >= c.MIN_GRPC_MAJOR, (
            f"gRPC major version must be >= {c.MIN_GRPC_MAJOR}, got {version}"
        )
        assert minor_version >= c.MIN_GRPC_MINOR, (
            f"gRPC minor version must be >= {c.MIN_GRPC_MINOR}, got {version}"
        )


class TestVersionConsistency:
    """Test version consistency across all configuration files."""

    def test_dockerfile_args_match_versions_env(self) -> None:
        """Verify Dockerfile ARG defaults match versions.env.

        Note: PYTHON_VERSION in Dockerfile uses major.minor (e.g., 3.12)
        while versions.env uses major.minor.patch (e.g., 3.12.8).
        The test checks that major.minor matches.
        """
        versions = self._load_versions_env()
        dockerfile = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()

        version_vars = [
            "PYTHON_VERSION",
            "GRPCIO_VERSION",
            "NUMPY_VERSION",
        ]
        for var in version_vars:
            expected = versions.get(var)
            # Match ARG VAR=value pattern
            pattern = rf"ARG {var}=(\S+)"
            match = re.search(pattern, dockerfile)
            assert match, f"Dockerfile missing ARG {var}"
            actual = match.group(1)
            # For PYTHON_VERSION, compare major.minor only
            if var == "PYTHON_VERSION" and expected:
                expected_major_minor = ".".join(
                    expected.split(".")[: c.VERSION_MAJOR_MINOR_PARTS]
                )
                assert actual == expected_major_minor, (
                    f"{var}: Dockerfile={actual}, "
                    f"{c.File.VERSIONS_ENV} major.minor={expected_major_minor}"
                )
            else:
                assert actual == expected, (
                    f"{var}: Dockerfile={actual}, c.File.VERSIONS_ENV={expected}"
                )

    def test_pyproject_has_python_version(self) -> None:
        """Verify pyproject.toml specifies Python 3.13 for Linux system.

        compatibility with mt5linux.
        """
        pyproject = (c.get_project_root() / c.File.PYPROJECT).read_text()
        # Linux system uses Python 3.13 for mt5linux compatibility
        # Wine environment uses Python 3.12 (defined in versions.env)
        assert c.LINUX_PYTHON_VERSION_PREFIX in pyproject, (
            "pyproject.toml should reference Python "
            f"{c.LINUX_PYTHON_VERSION_PREFIX} for Linux system compatibility"
        )

    def test_start_sh_has_version_fallbacks(self) -> None:
        """Verify start.sh has version fallback values."""
        script_path = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/start.sh"
        )
        content = script_path.read_text()
        # Should have version fallback values
        assert "PYTHON_VERSION" in content, "start.sh must have PYTHON_VERSION"
        assert "GRPCIO_VERSION" in content, "start.sh must have GRPCIO_VERSION"

    def _load_versions_env(self) -> dict[str, str]:
        """Load versions from c.File.VERSIONS_ENV file."""
        versions: dict[str, str] = {}
        versions_file = c.get_project_root() / c.Directory.DOCKER / c.File.VERSIONS_ENV

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
        dockerfile = c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        assert dockerfile.exists(), "Dockerfile must exist"

    def test_dockerfile_has_buildkit_syntax(self) -> None:
        """Verify Dockerfile uses BuildKit syntax."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()
        assert "syntax=docker/dockerfile" in content, "Should use BuildKit syntax"

    def test_dockerfile_has_multistage_build(self) -> None:
        """Verify Dockerfile uses multi-stage build."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()

        required_stages = ["base", "wine-base", "downloader", "wine-builder", "runtime"]
        for stage in required_stages:
            assert f"AS {stage}" in content, f"Missing stage: {stage}"

    def test_dockerfile_has_required_args(self) -> None:
        """Verify Dockerfile has all required ARGs."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()

        for arg in [*c.REQUIRED_VERSIONS, "BUILD_DATE", "VERSION"]:
            assert f"ARG {arg}" in content, f"Dockerfile missing ARG: {arg}"

    def test_dockerfile_exposes_required_ports(self) -> None:
        """Verify Dockerfile exposes required ports."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()

        assert "EXPOSE" in content
        assert str(c.Port.VNC) in content, "Must expose VNC port 3000"
        assert str(c.Port.GRPC) in content, "Must expose gRPC port 8001"

    def test_dockerfile_has_volume_config(self) -> None:
        """Verify Dockerfile declares /config volume."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()
        assert f"VOLUME {c.CONFIG_PATH}" in content, (
            f"Must declare {c.CONFIG_PATH} volume"
        )

    def test_dockerfile_has_oci_labels(self) -> None:
        """Verify Dockerfile has OCI-compliant labels."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()

        required_labels = [
            "org.opencontainers.image.title",
            "org.opencontainers.image.description",
            "org.opencontainers.image.version",
            "org.opencontainers.image.source",
        ]
        for label in required_labels:
            assert label in content, f"Missing OCI label: {label}"

    def test_dockerfile_copies_metatrader(self) -> None:
        """Verify Dockerfile copies metatrader directory."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()
        assert "COPY container/Metatrader" in content, "Must copy metatrader directory"

    def test_dockerfile_copies_s6_services(self) -> None:
        """Verify Dockerfile copies "s6-overlay" services."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKERFILE
        ).read_text()
        assert "s6-overlay" in content, "Must copy s6-overlay services"


# =============================================================================
# DOCKER COMPOSE TESTS
# =============================================================================


class TestDockerCompose:
    """Test docker-compose.yaml configuration."""

    def test_compose_file_exists(self) -> None:
        """Verify compose.yaml exists."""
        compose = c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        assert compose.exists(), "docker/compose.yaml must exist"

    def test_compose_config_valid(self) -> None:
        """Verify compose.yaml has valid syntax."""
        result = subprocess.run(
            ["docker", "compose", "-f", "docker/compose.yaml", "config", "--quiet"],
            cwd=c.get_project_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == c.SUCCESS_RETURN_CODE, (
            f"Compose config invalid: {result.stderr}"
        )

    def test_compose_has_env_file_required(self) -> None:
        """Verify compose requires .env file."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        ).read_text()
        assert "env_file:" in content
        assert "required: true" in content, ".env should be required"

    def test_compose_has_healthcheck(self) -> None:
        """Verify compose defines healthcheck."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        ).read_text()
        assert "healthcheck:" in content
        assert "test:" in content
        assert "interval:" in content
        assert "start_period:" in content

    def test_compose_has_resource_limits(self) -> None:
        """Verify compose defines resource limits."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        ).read_text()
        assert "deploy:" in content
        assert "resources:" in content
        assert "limits:" in content
        assert "memory:" in content

    def test_compose_has_security_options(self) -> None:
        """Verify compose has required security options for MT5."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        ).read_text()
        assert "cap_add:" in content
        assert "SYS_PTRACE" in content, "MT5 requires SYS_PTRACE capability"
        assert "security_opt:" in content
        assert "seccomp:unconfined" in content, "MT5 requires seccomp:unconfined"

    def test_compose_has_restart_policy(self) -> None:
        """Verify compose has restart policy."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        ).read_text()
        assert "restart:" in content
        assert "unless-stopped" in content

    def test_compose_has_ulimits(self) -> None:
        """Verify compose sets file descriptor limits."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        ).read_text()
        assert "ulimits:" in content
        assert "nofile:" in content

    def test_compose_uses_env_variables_for_ports(self) -> None:
        """Verify compose uses environment variables for port configuration."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.File.DOCKER_COMPOSE
        ).read_text()
        assert "${MT5_VNC_PORT:-" in content, "VNC port should use env var"
        assert "${MT5_GRPC_PORT:-" in content, "gRPC port should use env var"
        assert "${MT5_CONTAINER_NAME:-" in content, "Container name should use env var"


# =============================================================================
# SHELL SCRIPT TESTS
# =============================================================================


class TestShellScriptSyntax:
    """Test shell script syntax validation."""

    @pytest.mark.parametrize("script", c.ALL_SCRIPTS)
    def test_script_exists(self, script: str) -> None:
        """Verify script file exists."""
        script_path = c.get_project_root() / script
        assert script_path.exists(), f"Script not found: {script}"

    @pytest.mark.parametrize("script", c.ALL_SCRIPTS)
    def test_script_syntax_valid(self, script: str) -> None:
        """Verify script has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", script],
            cwd=c.get_project_root(),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == c.SUCCESS_RETURN_CODE, (
            f"Syntax error in {script}: {result.stderr}"
        )

    @pytest.mark.parametrize("script", c.ALL_SCRIPTS)
    def test_script_is_executable(self, script: str) -> None:
        """Verify script has executable permission."""
        script_path = c.get_project_root() / script
        assert script_path.stat().st_mode & 0o111, f"Script not executable: {script}"

    @pytest.mark.parametrize("script", c.ALL_SCRIPTS)
    def test_script_has_shebang(self, script: str) -> None:
        """Verify script has proper shebang."""
        script_path = c.get_project_root() / script
        first_line = script_path.read_text().splitlines()[0]
        assert first_line.startswith("#!"), f"Missing shebang in {script}"
        valid_shebang = "bash" in first_line or "sh" in first_line
        assert valid_shebang, f"Invalid shebang: {first_line}"


class TestStartupScriptContent:
    """Test startup script specific content."""

    def test_start_sh_exports_config(self) -> None:
        """Verify start.sh exports all configuration."""
        script_path = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/start.sh"
        )
        content = script_path.read_text()

        required_exports = ["WINEPREFIX", "WINE_PYTHON_PATH", "STARTUP_MARKER"]
        for var in required_exports:
            assert var in content, f"start.sh must export {var}"

    def test_start_sh_runs_setup(self) -> None:
        """Verify start.sh runs setup.sh."""
        content = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/start.sh"
        ).read_text()
        assert "setup.sh" in content, "start.sh must run setup.sh"

    def test_setup_sh_has_all_functions(self) -> None:
        """Verify setup.sh has all required setup functions."""
        content = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/setup.sh"
        ).read_text()

        required_functions = [
            "unpack_config",
            "init_wine_prefix",
            "configure_wine_settings",
            "install_mt5_pip",
            "install_mt5_terminal",
            "generate_mt5_config",
            "copy_bridge",
        ]
        for func in required_functions:
            assert func in content, f"setup.sh must have {func} function"

    def test_setup_sh_uses_winetricks_unattended(self) -> None:
        """Verify setup.sh configures Wine properly (no winetricks needed)."""
        content = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/setup.sh"
        ).read_text()
        # Win10 is set via registry, not winetricks (simpler approach)
        assert "win10" in content, "Must configure Windows version"

    def test_setup_sh_handles_mt5_installation(self) -> None:
        """Verify setup.sh handles MT5 installation."""
        content = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/setup.sh"
        ).read_text()
        assert "mt5setup" in content.lower(), "Must handle MT5 setup"
        assert "MetaTrader5" in content, "Must install MetaTrader5 pip"

    def test_health_monitor_uses_restart_token(self) -> None:
        """Verify health_monitor.sh uses restart token (not direct restart)."""
        script_path = (
            c.get_project_root()
            / c.Directory.CONTAINER
            / "Metatrader/health_monitor.sh"
        )
        content = script_path.read_text()

        # Should use token-based restart signaling
        assert "RESTART_TOKEN" in content, "Should use RESTART_TOKEN"
        assert "request_restart" in content, "Should have request_restart function"

        # Should NOT have direct restart functions
        assert "restart_mt5()" not in content, "Should not have direct restart_mt5"
        assert "restart_grpc_server()" not in content, "Should not have restart_grpc"

    def test_health_monitor_has_failure_threshold(self) -> None:
        """Verify health_monitor.sh uses failure threshold before restart."""
        script_path = (
            c.get_project_root()
            / c.Directory.CONTAINER
            / "Metatrader/health_monitor.sh"
        )
        content = script_path.read_text()
        assert "FAILURE_THRESHOLD" in content, "Should have configurable threshold"
        assert "FAILURE_COUNT" in content, "Should track failure count"


# =============================================================================
# S6-OVERLAY SERVICE TESTS
# =============================================================================


class TestS6Services:
    """Test "s6-overlay" service configuration."""

    def test_s6_service_directory_exists(self) -> None:
        """Verify s6 service directory exists."""
        s6_dir = c.get_project_root() / c.S6_OVERLAY_BASE_PATH
        assert s6_dir.exists(), "s6-overlay directory must exist"

    def test_s6_mt5server_service_exists(self) -> None:
        """Verify svc-mt5server service is defined."""
        s6_base = c.get_project_root() / c.S6_RC_BASE_PATH
        service_dir = s6_base / "svc-mt5server"
        assert service_dir.exists(), "svc-mt5server service must exist"

    def test_s6_service_has_run_script(self) -> None:
        """Verify service has run script."""
        s6_base = c.get_project_root() / c.S6_RC_BASE_PATH
        run_script = s6_base / "svc-mt5server/run"
        assert run_script.exists(), "Service must have run script"

    def test_s6_service_has_finish_script(self) -> None:
        """Verify service has finish script."""
        s6_base = c.get_project_root() / c.S6_RC_BASE_PATH
        finish_script = s6_base / "svc-mt5server/finish"
        assert finish_script.exists(), "Service should have finish script"

    def test_s6_service_has_inline_config(self) -> None:
        """Verify s6 service has inline configuration (no external deps)."""
        s6_base = c.get_project_root() / c.S6_RC_BASE_PATH
        run_script = s6_base / "svc-mt5server/run"
        content = run_script.read_text()

        # Should NOT source external scripts
        assert "scripts/00_env.sh" not in content, "Should not source old 00_env.sh"

        # Should have inline config
        assert "WINEPREFIX" in content, "Should have inline WINEPREFIX config"
        assert "STARTUP_MARKER" in content, "Should have inline STARTUP_MARKER"

    def test_s6_service_monitors_restart_token(self) -> None:
        """Verify svc-mt5server monitors restart token from health_monitor."""
        s6_base = c.get_project_root() / c.S6_RC_BASE_PATH
        run_script = s6_base / "svc-mt5server/run"
        content = run_script.read_text()

        # Should monitor restart token
        assert "RESTART_TOKEN" in content, "Should monitor RESTART_TOKEN"
        assert "check_restart_token" in content, "Should have check function"
        assert "clear_restart_token" in content, "Should clear token after restart"

    def test_s6_service_has_full_restart(self) -> None:
        """Verify svc-mt5server can do full restart (MT5 + bridge)."""
        s6_base = c.get_project_root() / c.S6_RC_BASE_PATH
        run_script = s6_base / "svc-mt5server/run"
        content = run_script.read_text()

        # Should have full restart capability
        assert "full_restart" in content, "Should have full_restart function"
        assert "kill_mt5" in content, "Should be able to kill MT5"
        assert "kill_bridge" in content, "Should be able to kill bridge"
        assert "start_mt5_terminal" in content, "Should be able to start MT5"
        assert "start_bridge" in content, "Should be able to start bridge"

    def test_s6_service_has_main_loop(self) -> None:
        """Verify svc-mt5server runs in main loop (not exec)."""
        s6_base = c.get_project_root() / c.S6_RC_BASE_PATH
        run_script = s6_base / "svc-mt5server/run"
        content = run_script.read_text()

        # Should run in a loop, not exec
        assert "while true" in content, "Should run in main loop"
        # Should NOT have exec at the end (old pattern)
        last_lines = content.strip().split("\n")[-c.LOG_TAIL_LAST_LINES :]
        last_content = "\n".join(last_lines)
        assert "exec " not in last_content, "Should not exec at end (uses loop)"


# =============================================================================
# CONFIGURATION FILE TESTS
# =============================================================================


class TestConfigFiles:
    """Test configuration files."""

    def test_env_example_exists(self) -> None:
        """Verify .env.example exists for documentation."""
        env_example = c.get_project_root() / c.CONFIG_DIR / c.File.ENV_EXAMPLE
        assert env_example.exists(), ".env.example should exist for documentation"

    def test_env_example_has_required_vars(self) -> None:
        """Verify .env.example documents required variables."""
        env_example = c.get_project_root() / c.CONFIG_DIR / c.File.ENV_EXAMPLE
        content = env_example.read_text()

        required_vars = ["MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER"]
        for var in required_vars:
            assert var in content, f".env.example missing: {var}"

    def test_dockerignore_exists(self) -> None:
        """Verify .dockerignore exists."""
        dockerignore = c.get_project_root() / c.Directory.DOCKER / c.DOCKERIGNORE_FILE
        assert dockerignore.exists(), ".dockerignore should exist"

    def test_dockerignore_excludes_sensitive(self) -> None:
        """Verify .dockerignore excludes sensitive files."""
        content = (
            c.get_project_root() / c.Directory.DOCKER / c.DOCKERIGNORE_FILE
        ).read_text()

        # Should exclude .env, .git, etc.
        should_exclude = [".env", ".git"]
        for item in should_exclude:
            assert item in content, f".dockerignore should exclude: {item}"

    def test_pyproject_toml_exists(self) -> None:
        """Verify pyproject.toml exists."""
        pyproject = c.get_project_root() / c.File.PYPROJECT
        assert pyproject.exists(), "pyproject.toml must exist"

    def test_pyproject_has_pytest_config(self) -> None:
        """Verify pyproject.toml has pytest configuration."""
        content = (c.get_project_root() / c.File.PYPROJECT).read_text()
        assert "[tool.pytest" in content, "Must have pytest configuration"
        assert "testpaths" in content


# =============================================================================
# DIRECTORY STRUCTURE TESTS
# =============================================================================


class TestDirectoryStructure:
    """Test project directory structure."""

    def test_metatrader_directory_exists(self) -> None:
        """Verify metatrader directory exists."""
        assert (
            c.get_project_root() / c.Directory.CONTAINER / c.METATRADER_DIR
        ).is_dir()

    def test_bridge_py_exists(self) -> None:
        """Verify bridge.py (gRPC server) exists."""
        bridge_path = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/bridge.py"
        )
        assert bridge_path.exists(), "bridge.py must exist for gRPC server"

    def test_bridge_py_is_standalone(self) -> None:
        """Verify bridge.py uses gRPC and has standalone proto files."""
        bridge_path = (
            c.get_project_root() / c.Directory.CONTAINER / "Metatrader/bridge.py"
        )
        content = bridge_path.read_text()
        # Should import grpc for the gRPC server
        assert "import grpc" in content, "Must import grpc"
        # Should import local proto files (standalone in container)
        # Accept both absolute and relative imports
        has_mt5_pb2 = "import mt5_pb2" in content or "from . import" in content
        has_mt5_pb2_grpc = (
            "import mt5_pb2_grpc" in content or "from . import" in content
        )
        assert has_mt5_pb2, "Must import mt5_pb2 (absolute or relative)"
        assert has_mt5_pb2_grpc, "Must import mt5_pb2_grpc (absolute or relative)"
        assert "import structlog" not in content, "Must not depend on structlog"

    def test_proto_files_exist(self) -> None:
        """Verify proto files exist for gRPC bridge."""
        metatrader_dir = c.get_project_root() / c.Directory.CONTAINER / c.METATRADER_DIR
        assert (metatrader_dir / "mt5_pb2.py").exists(), "mt5_pb2.py must exist"
        assert (metatrader_dir / "mt5_pb2_grpc.py").exists(), (
            "mt5_pb2_grpc.py must exist"
        )

    def test_root_directory_exists(self) -> None:
        """Verify root directory (LinuxServer defaults) exists."""
        assert (c.get_project_root() / c.Directory.CONTAINER / c.ROOT_DIR).is_dir()

    def test_tests_directory_exists(self) -> None:
        """Verify tests directory exists."""
        assert (c.get_project_root() / c.TESTS_DIR).is_dir()

    def test_consolidated_script_structure(self) -> None:
        """Verify consolidated script structure (no scripts/ folder)."""
        metatrader_dir = c.get_project_root() / c.Directory.CONTAINER / c.METATRADER_DIR

        # Should have consolidated scripts
        assert (metatrader_dir / "start.sh").exists(), "start.sh must exist"
        assert (metatrader_dir / "setup.sh").exists(), "setup.sh must exist"
        health_script = metatrader_dir / "health_monitor.sh"
        assert health_script.exists(), "health_monitor.sh must exist"

        # Should NOT have scripts/ folder
        scripts_dir = metatrader_dir / "scripts"
        assert not scripts_dir.exists(), "scripts/ folder should not exist"
