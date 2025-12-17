"""Centralized test constants for MT5Docker container tests.

This module contains all magic numbers, default values, and configuration constants
used throughout the mt5docker test suite. Organized by business domains with
advanced patterns.

Advanced patterns used:
- StrEnum for string enumerations (business-focused, organized within namespaces)
- IntEnum for integer enumerations (business-focused, organized within namespaces)
- Final constants for immutable values
- Literal types for restricted string values
- Frozen sets for immutable collections
- Typed mappings for structured constants

Business Domain Namespaces (ONLY business domains, enums nested within):
- Project: Project structure, paths, and helper methods
- Infrastructure: Container, Docker, ports, services
- Timing: Timeouts, health checks, waits
- Testing: Test tokens, paths, return codes, command execution
- Versioning: Version requirements, file names, version checking
- Message: Skip messages and user-facing text
- Financial: Trading data and financial parameters
- Risk: Risk management parameters
- Signal: Trading signal parameters (with IndicatorType enum)
- Order: Order execution (with OrderMechanism, OrderStatus, RouterPriority enums)
- Backtest: Backtesting parameters
- ML: Machine learning parameters
- Trading: Trade/market domain (SignalType enum)
- Kafka: Message queue config (CompressionType, AcksMode enums)
- Logging: Log configuration (LogLevelType enum)
- TestData: Test data generation (IssueType, TrendType enums)
- Environment: Environment types (EnvironmentType enum)

Usage:
    from tests.constants import TestConstants as c

    # Infrastructure constants
    port = c.MT5.GRPC_PORT
    timeout = c.Network.SOCKET_TIMEOUT

    # Enum access (via business namespace)
    compression = c.Kafka.CompressionType.GZIP
    signal = c.Trading.SignalType.BUY
    indicator = c.Signal.IndicatorType.RSI

    # Project paths
    root = c.Project.get_project_root()
    docker_dir = root / c.Directory.DOCKER

    # Testing constants
    test_port = c.TestRunner.GRPC_PORT
    cmd_timeout = c.TestRunner.COMMAND_TIMEOUT
"""

from __future__ import annotations

import os
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Final

# =============================================================================
# MAIN TEST CONSTANTS CLASS (ONLY NESTED CLASS)
# =============================================================================


class TestConstants:
    """Centralized constants for all mt5docker tests.

    Business domain-organized namespaces with enums nested within:
    - StrEnum/IntEnum classes nested within business domain namespaces
    - Final constants for immutable values
    - Frozen sets for immutable collections
    - Typed mappings for structured constants

    All constants accessed directly via c.* (no additional aliases).
    NO helpers inside the class - only data constants.
    NO top-level enum classes - all enums nested in business domains.
    """

    # =========================================================================
    # PROJECT NAMESPACE - Project structure and paths
    # =========================================================================

    class Project:
        """Project structure, paths, and utilities."""

        @staticmethod
        def get_project_root() -> Path:
            """Get mt5docker project root directory."""
            return Path(__file__).parent.parent

    class Directory:
        """Directory names within project structure."""

        DOCKER: Final = "docker"
        CONTAINER: Final = "docker/container"  # Full path from project root
        METATRADER: Final = "Metatrader"
        TESTS: Final = "tests"
        SCRIPTS: Final = "scripts"
        CONFIG: Final = "config"
        S6_OVERLAY: Final = "docker/container/Metatrader/etc/s6-overlay"
        S6_RC: Final = "docker/container/Metatrader/etc/s6-overlay/s6-rc.d"

    class File:
        """File names and patterns."""

        VERSIONS_ENV: Final = "versions.env"
        DOCKER_COMPOSE: Final = "compose.yaml"  # compose.yaml (not docker-compose.yaml)
        DOCKERFILE: Final = "Dockerfile"
        DOCKERFILE_DEV: Final = "Dockerfile.dev"
        ENV_EXAMPLE: Final = ".env.example"
        ENV_FILE: Final = ".env"
        PYPROJECT: Final = "pyproject.toml"
        DOCKERIGNORE: Final = ".dockerignore"
        S6_SERVICE_DIR: Final = "docker/container/Metatrader/etc/s6-overlay/s6-rc.d"

    class Scripts:
        """Shell scripts in the project."""

        # All shell scripts relative to project root
        ALL_SCRIPTS: Final[tuple[str, ...]] = (
            "docker/container/Metatrader/health_monitor.sh",
            "docker/container/Metatrader/setup.sh",
            "docker/container/Metatrader/start.sh",
            "scripts/setup-dependencies.sh",
        )

        # Main container startup scripts (at root, not /app)
        CONTAINER_MAIN_SCRIPTS: Final[tuple[str, ...]] = (
            "/Metatrader/health_monitor.sh",
            "/Metatrader/setup.sh",
            "/Metatrader/start.sh",
        )

    # =========================================================================
    # ENVIRONMENT NAMESPACE - Environment types and configuration
    # =========================================================================

    class Environment:
        """Environment configuration with nested enum."""

        class EnvironmentType(StrEnum):
            """Application environment types."""

            DEVELOPMENT = "development"
            TESTING = "testing"
            STAGING = "staging"
            PRODUCTION = "production"

        # Expose enum for access
        TYPES = EnvironmentType

    # =========================================================================
    # INFRASTRUCTURE NAMESPACE - Container and service configuration
    # =========================================================================

    class MT5:
        """MT5 Docker and connection constants."""

        GRPC_PORT: Final[int] = int(os.getenv("MT5_GRPC_PORT", "48812"))
        VNC_PORT: Final[int] = int(os.getenv("MT5_VNC_PORT", "43000"))
        HEALTH_PORT: Final[int] = int(os.getenv("MT5_HEALTH_PORT", "48002"))
        STARTUP_TIMEOUT: Final[int] = int(os.getenv("MT5_STARTUP_TIMEOUT", "420"))
        TIMEOUT: Final[int] = 60

    class Connection:
        """Connection and API constants."""

        TIMEOUT: Final[int] = 60
        TIMEOUT_MS: Final[int] = 60000  # 60s in milliseconds
        IPC_TIMEOUT_ERROR: Final[int] = -10005

    class Database:
        """Database connection constants."""

        POSTGRES_PORT: Final[int] = 5432
        POSTGRES_HOST: Final = "localhost"
        POSTGRES_TEST_DATABASE: Final = "test_db"
        POSTGRES_TEST_USER: Final = "test_user"
        CLICKHOUSE_PORT: Final[int] = 9000
        MAX_CONNECTIONS: Final[int] = 20
        CONNECTION_TIMEOUT: Final[int] = 30
        CUSTOM_CLICKHOUSE_PORT: Final[int] = 9001
        CUSTOM_POSTGRES_PORT: Final[int] = 5433
        CUSTOM_MAX_CONNECTIONS: Final[int] = 50

    class Kafka:
        """Kafka configuration constants with nested enums."""

        class CompressionType(StrEnum):
            """Kafka compression types."""

            NONE = "none"
            GZIP = "gzip"
            SNAPPY = "snappy"
            LZ4 = "lz4"
            ZSTD = "zstd"

        class AcksMode(StrEnum):
            """Kafka acknowledgment modes."""

            ZERO = "0"
            ONE = "1"
            ALL = "all"
            LEADER = "-1"

        BOOTSTRAP_SERVERS: Final[tuple[str, ...]] = ("localhost:9092",)
        PORT: Final[int] = 9092
        HOST: Final = "localhost"
        DEFAULT_RETRIES: Final[int] = 3
        CUSTOM_RETRIES: Final[int] = 5
        CONNECTION_TIMEOUT: Final[float] = 2.0

    class Network:
        """Network and connection constants."""

        SOCKET_TIMEOUT: Final[float] = 2.0
        GRPC_DEFAULT_TIMEOUT: Final[float] = 10.0
        GRPC_STARTUP_TIMEOUT: Final[float] = 30.0
        PORT_CHECK_MAX_ATTEMPTS: Final[int] = 3

    # =========================================================================
    # TIMING NAMESPACE - Timeouts, health checks, waits
    # =========================================================================

    class Timing:
        """Timing and retry constants."""

        MIN_RETRY_INTERVAL: Final[float] = 0.5
        MAX_RETRY_INTERVAL: Final[float] = 5.0
        RETRY_BACKOFF_MULTIPLIER: Final[float] = 1.5
        DOCKER_START_TIMEOUT: Final[int] = 300

    class HealthCheck:
        """Health check timing constants."""

        STARTUP_TIMEOUT: Final[int] = 10  # gRPC startup health check timeout
        FAST_PATH_TIMEOUT: Final[float] = 2.0  # Quick health check timeout

    # =========================================================================
    # TESTING NAMESPACE - Test execution, tokens, paths, return codes
    # =========================================================================

    class TestRunner:
        """Test execution and runtime constants."""

        GRPC_PORT: Final[int] = 48812
        TIMEOUT: Final[int] = 60
        COMMAND_TIMEOUT: Final[int] = 30
        SUCCESS_RETURN_CODE: Final[int] = 0
        FAILURE_RETURN_CODE: Final[int] = 1
        MAX_RANGE_RETRIES: Final[int] = 3

        # Test infrastructure paths
        TMP_PATH: Final = "/tmp"  # noqa: S108
        RESTART_TEST_TOKEN_FILE: Final = "mt5docker_restart_token"  # noqa: S105

        # Container logging
        LOG_TAIL_LINES: Final[int] = 100
        LOG_TAIL_LAST_LINES: Final[int] = 5  # Last N lines to check for patterns
        MAX_LOG_LENGTH: Final[int] = 5000

    class TestContainer:
        """Test container configuration."""

        NAME: Final = "mt5docker-test"
        CONTAINER_DIR: Final = "/app"
        METATRADER_DIR: Final = "Metatrader"
        NETWORK_SUFFIX: Final = "-network"
        VOLUME_SUFFIX: Final = "-data"
        MAX_RESTARTS: Final[int] = 3
        CONFIG_VOLUME_PATH: Final = "/config"  # Volume mount point inside container
        CONFIG_PATH: Final = "/config"  # Volume mount point inside container

    # =========================================================================
    # GRPC SERVICE NAMESPACE - gRPC server configuration
    # =========================================================================

    class GRPCService:
        """gRPC service and bridge constants."""

        HOST: Final = "0.0.0.0"  # noqa: S104
        PORT: Final[int] = 50051
        WORKERS: Final[int] = 10
        CHUNK_SIZE: Final[int] = 500  # Symbol chunk size for large datasets
        SHUTDOWN_GRACE_PERIOD: Final[int] = 5  # Seconds to wait for graceful shutdown

    # =========================================================================
    # VERSIONING NAMESPACE - Version requirements and checking
    # =========================================================================

    class Versioning:
        """Version requirements and configuration."""

        VERSION_PARTS_COUNT: Final[int] = 3  # Major.Minor.Patch
        MIN_CONSTANTS_COUNT: Final[int] = 50  # Minimum MT5 constants expected
        MIN_LOGIN_VALUE: Final[int] = 0  # Minimum valid login

        # Required ARG versions in Dockerfile (subset of versions.env)
        # Note: versions.env has more vars, but only these are ARGs in Dockerfile
        REQUIRED_VERSIONS: Final[frozenset[str]] = frozenset(
            {
                "PYTHON_VERSION",
                "GRPCIO_VERSION",
                "NUMPY_VERSION",
                "WINE_MONO_VERSION",
                "WINE_GECKO_VERSION",
            }
        )

    class Paths:
        """Full paths for validation tests."""

        ROOT_DIR: Final = ""  # Empty - used with Directory.CONTAINER to form full path
        TESTS_DIR: Final = "tests"
        CONFIG_DIR: Final = "config"
        S6_OVERLAY_BASE_PATH: Final = "docker/container/Metatrader/etc/s6-overlay"
        S6_RC_BASE_PATH: Final = "docker/container/Metatrader/etc/s6-overlay/s6-rc.d"
        # Linux system Python version in pyproject.toml
        LINUX_PYTHON_VERSION_PREFIX: Final = "3.13"

    class Port(IntEnum):
        """Docker exposed ports."""

        VNC = 3000  # KasmVNC port
        GRPC = 8001  # gRPC bridge port

    class VersionCheck:
        """Version string patterns and prefixes with nested enums."""

        class Prefix(StrEnum):
            """Version string prefixes for validation."""

            PYTHON = "3.12"  # Major.Minor from versions.env
            NUMPY = "1.26"
            MT5 = "5.0"  # MetaTrader5 package version
            GRPC = "1.7"

        MT5_VERSION_PREFIX: Final = Prefix.MT5  # "5.0" format
        # "3.12" format (from versions.env - Windows/Wine side)
        PYTHON_VERSION_PREFIX: Final = Prefix.PYTHON
        NUMPY_VERSION_PREFIX: Final = Prefix.NUMPY  # "1.26" format
        GRPC_VERSION_PREFIX: Final = Prefix.GRPC  # "1.7" format
        # Linux system Python (Debian) - for display/validation
        PYTHON_VERSION_STRING: Final = "Python 3.11"
        PYTHON_VERSION_PATTERN: Final = r"Python \d+\.\d+\.\d+"

        # Version parsing
        VERSION_MAJOR_MINOR_PARTS: Final[int] = 2
        MIN_GRPC_MAJOR: Final[int] = 1
        MIN_GRPC_MINOR: Final[int] = 7

    # =========================================================================
    # MESSAGE NAMESPACE - User-facing messages and text constants
    # =========================================================================

    class Message:
        """User-facing messages and skip messages."""

        SKIP_NO_CREDENTIALS: Final = (
            "MT5 credentials not configured in .env file. "
            "Set MT5_LOGIN, MT5_PASSWORD, and MT5_SERVER to run container tests."
        )
        SKIP_NO_COMPOSE_FILE: Final = "docker-compose.yaml not found"
        SKIP_NO_CONTAINER: Final = "Container not running - skipping container tests"

    # =========================================================================
    # FINANCIAL & TRADING CONSTANTS
    # =========================================================================

    class Financial:
        """Financial and trading constants."""

        DEFAULT_BASE_PRICE: Final[float] = 1.1000
        DEFAULT_SYMBOL: Final = "EURUSD"
        DEFAULT_VOLUME: Final[float] = 0.1
        DEFAULT_SL_PERCENTAGE: Final[float] = 0.005  # 0.5%
        DEFAULT_TP_PERCENTAGE: Final[float] = 0.005  # 0.5%
        PRICE_VOLATILITY: Final[float] = 0.001
        PRICE_NOISE: Final[float] = 0.0008
        HIGH_LOW_SPREAD: Final[float] = 0.0005
        VOLUME_MIN: Final[int] = 1000
        VOLUME_MAX: Final[int] = 10000
        SYMBOL_POINT_DEFAULT: Final[float] = 0.00001
        VOLUME_MIN_DEFAULT: Final[float] = 0.01
        VOLUME_MAX_DEFAULT: Final[float] = 1000.0
        VOLUME_STEP_DEFAULT: Final[float] = 0.01
        CONTRACT_SIZE_DEFAULT: Final[int] = 100000
        MARGIN_REQUIRED_DEFAULT: Final[float] = 1000.0

    class Risk:
        """Risk management constants with nested profile types."""

        class ProfileType(StrEnum):
            """Risk profile types."""

            CONSERVATIVE = "CONSERVATIVE"
            MODERATE = "MODERATE"
            AGGRESSIVE = "AGGRESSIVE"
            CUSTOM = "CUSTOM"

        MAX_POSITION_SIZE_DEFAULT: Final[float] = 0.05
        MAX_PORTFOLIO_RISK_DEFAULT: Final[float] = 0.02
        MAX_DRAWDOWN_DEFAULT: Final[float] = 0.15
        MAX_POSITIONS_DEFAULT: Final[int] = 10
        MAX_LEVERAGE_DEFAULT: Final[float] = 1.0
        CUSTOM_MAX_POSITION_SIZE: Final[float] = 0.1
        CUSTOM_MAX_PORTFOLIO_RISK: Final[float] = 0.05
        CUSTOM_MAX_POSITIONS: Final[int] = 20
        INVALID_MAX_POSITION_SIZE: Final[float] = 0.5
        INVALID_MAX_PORTFOLIO_RISK: Final[float] = 0.15
        INVALID_MAX_DRAWDOWN: Final[float] = 0.6

    class Signal:
        """Trading signal configuration constants with nested indicator types."""

        class IndicatorType(StrEnum):
            """Technical indicator types."""

            RSI = "RSI"
            MACD = "MACD"
            BOLLINGER_BANDS = "BOLLINGER_BANDS"
            SMA = "SMA"
            EMA = "EMA"
            STOCHASTIC = "STOCHASTIC"
            ADX = "ADX"
            ATR = "ATR"
            WILLIAMS_R = "WILLIAMS_R"
            CCI = "CCI"

        DEFAULT_CONFIDENCE: Final[float] = 0.8
        SIGNAL_STOP_LOSS_FACTOR: Final[float] = 0.995  # 0.5% below entry
        SIGNAL_TAKE_PROFIT_FACTOR: Final[float] = 1.02  # 2% above entry
        RSI_OVERSOLD_DEFAULT: Final[float] = 30.0
        RSI_OVERBOUGHT_DEFAULT: Final[float] = 70.0
        RSI_PERIOD_DEFAULT: Final[int] = 14
        MACD_FAST_DEFAULT: Final[int] = 12
        MACD_SLOW_DEFAULT: Final[int] = 26
        MACD_SIGNAL_DEFAULT: Final[int] = 9
        MIN_CONFIDENCE_DEFAULT: Final[float] = 0.6
        CUSTOM_RSI_OVERSOLD: Final[float] = 25.0
        CUSTOM_RSI_OVERBOUGHT: Final[float] = 75.0
        CUSTOM_MIN_CONFIDENCE: Final[float] = 0.7
        INVALID_RSI_OVERSOLD: Final[float] = -5.0
        INVALID_RSI_OVERBOUGHT: Final[float] = 105.0
        INVALID_MIN_CONFIDENCE: Final[float] = 0.3

    class Order:
        """Order execution constants with nested enums."""

        class Mechanism(StrEnum):
            """Order execution mechanisms."""

            MARKET = "MARKET"
            LIMIT = "LIMIT"
            STOP = "STOP"
            STOP_LIMIT = "STOP_LIMIT"
            TRAILING_STOP = "TRAILING_STOP"

        class Status(StrEnum):
            """Order lifecycle status."""

            PENDING = "PENDING"
            SUBMITTED = "SUBMITTED"
            FILLED = "FILLED"
            PARTIALLY_FILLED = "PARTIALLY_FILLED"
            REJECTED = "REJECTED"
            CANCELLED = "CANCELLED"
            EXPIRED = "EXPIRED"

        class Priority(IntEnum):
            """Order router priority levels."""

            LOW = 1
            HIGH = 2

        ROUTER_DEFAULT_LATENCY: Final[float] = 0.0
        ROUTER_DEFAULT_SUCCESS_RATE: Final[float] = 1.0
        ROUTER_HIGH_LATENCY: Final[float] = 15.5
        ROUTER_MEDIUM_SUCCESS_RATE: Final[float] = 0.98
        ROUTER_ROUTING_COST: Final[float] = 0.001
        ROUTER_SUCCESS_PROBABILITY: Final[float] = 0.95

    class Trading:
        """Trading domain with signal types."""

        class SignalType(StrEnum):
            """Trading signal types."""

            BUY = "BUY"
            SELL = "SELL"
            HOLD = "HOLD"

    # =========================================================================
    # TESTING & ML CONSTANTS
    # =========================================================================

    class Backtest:
        """Backtesting configuration constants."""

        INITIAL_CAPITAL_DEFAULT: Final[float] = 100000.0
        COMMISSION_DEFAULT: Final[float] = 0.001
        SLIPPAGE_DEFAULT: Final[float] = 0.0001
        RISK_FREE_RATE_DEFAULT: Final[float] = 0.02
        CUSTOM_MAX_POSITION_SIZE_BT: Final[float] = 0.10
        CUSTOM_INITIAL_CAPITAL: Final[float] = 50000.0
        CUSTOM_COMMISSION: Final[float] = 0.002
        INVALID_INITIAL_CAPITAL: Final[float] = 0.0
        INVALID_COMMISSION: Final[float] = 1.5
        INVALID_RISK_FREE_RATE: Final[float] = -0.1
        DURATION_DAYS_DEFAULT: Final[int] = 365
        FINAL_CAPITAL_DEFAULT: Final[float] = 110000.0
        TOTAL_RETURN_DEFAULT: Final[float] = 0.10

    class ML:
        """Machine learning training constants."""

        TRAIN_SIZE_DEFAULT: Final[float] = 0.8
        VALIDATION_SIZE_DEFAULT: Final[float] = 0.1
        TEST_SIZE_DEFAULT: Final[float] = 0.1
        RANDOM_STATE: Final[int] = 42
        LOOKBACK_PERIODS: Final[int] = 5
        TREND_DEFAULT: Final[float] = 0.00001
        CUSTOM_TRAIN_SIZE: Final[float] = 0.7
        CUSTOM_VALIDATION_SIZE: Final[float] = 0.15
        CUSTOM_TEST_SIZE: Final[float] = 0.15
        INVALID_TRAIN_SIZE_SUM: Final[float] = 0.5
        INVALID_VALIDATION_SIZE_SUM: Final[float] = 0.3
        INVALID_TEST_SIZE_SUM: Final[float] = 0.3
        VALID_TRAIN_SIZE: Final[float] = 0.6
        VALID_VALIDATION_SIZE: Final[float] = 0.2
        VALID_TEST_SIZE: Final[float] = 0.2

    class Prediction:
        """ML prediction constants."""

        CONFIDENCE_THRESHOLD_DEFAULT: Final[float] = 0.6
        CONFIDENCE_THRESHOLD_HIGH: Final[float] = 0.8
        CONFIDENCE_THRESHOLD_LOW: Final[float] = 0.5
        CONFIDENCE_THRESHOLD_MAX: Final[float] = 1.0
        CONFIDENCE_THRESHOLD_INVALID_LOW: Final[float] = -0.1
        CONFIDENCE_THRESHOLD_INVALID_HIGH: Final[float] = 1.1

    class Benchmark:
        """Performance benchmarking constants."""

        ITERATIONS: Final[int] = 100
        PERF_P99_PERCENTILE: Final[float] = 0.99
        CACHE_TTL_DEFAULT: Final[float] = 60.0

    # =========================================================================
    # TEST DATA & VALIDATION CONSTANTS
    # =========================================================================

    class TestData:
        """Test data generation and validation constants with nested enums."""

        class IssueType(StrEnum):
            """Test data issue types."""

            INVALID_OHLC = "invalid_ohlc"
            NEGATIVE_PRICES = "negative_prices"
            MISSING_DATA = "missing_data"

        class TrendType(StrEnum):
            """Test data trend types."""

            UPWARD = "upward"
            DOWNWARD = "downward"
            SIDEWAYS = "sideways"

        DEFAULT_PERIODS: Final[int] = 100
        MARKET_DATA_DAYS: Final[int] = 30
        TEST_PERIODS_VALID: Final[int] = 50
        TEST_PERIODS_EMPTY: Final[int] = 0
        TEST_PERIODS_SMALL: Final[int] = 20
        INTEGRATION_PERIODS_DEFAULT: Final[int] = 100
        INTEGRATION_PERIODS_SMALL: Final[int] = 20
        OHLC_INVALID_THRESHOLD: Final[int] = 0
        INVALID_HIGH_PRICE: Final[float] = 1.0990
        INVALID_LOW_PRICE: Final[float] = 1.0985
        INVALID_CLOSE_PRICE: Final[float] = 1.1005
        TREND_UP_VALUE: Final[float] = 0.0001
        TREND_DOWN_VALUE: Final[float] = -0.0001
        TREND_SIDEWAYS_VALUE: Final[float] = 0.0
        VOLATILITY_LOW: Final[float] = 0.0001
        VOLATILITY_MEDIUM: Final[float] = 0.0005
        PRICE_INCREMENT: Final[float] = 0.0001
        HIGH_LOW_SPREAD_SU: Final[float] = 0.0005
        CLOSE_ADJUSTMENT: Final[float] = 0.0002
        BASE_VOLUME_SU: Final[int] = 1000

    class Validation:
        """Data validation constants."""

        MODEL_SIZE_MIN_BYTES: Final[int] = 0
        TEST_TIMEOUT_SECONDS: Final[int] = 120
        TEST_EXECUTION_TIMEOUT: Final[int] = 120
        STDOUT_TRUNCATE_LENGTH: Final[int] = 1000

    class Logging:
        """Logging configuration constants with nested enum."""

        class LevelType(StrEnum):
            """Logging level types."""

            DEBUG = "DEBUG"
            INFO = "INFO"
            WARNING = "WARNING"
            ERROR = "ERROR"
            CRITICAL = "CRITICAL"

        MIN_LOGGER_HANDLERS: Final[int] = 1
        MIN_LOGGER_HANDLERS_WITH_FILE: Final[int] = 2

    # =========================================================================
    # COLLECTIONS & ENUMERATIONS (Must be after all namespaces are defined)
    # =========================================================================

    class Collections:
        """Immutable collections for test configuration."""

        # These are populated from enums after class definition
        COMPRESSION_TYPES: frozenset[str]
        ACKS_MODES: frozenset[str]

        SAFE_TEST_SYMBOLS: Final[tuple[str, ...]] = (
            "EURUSD",
            "GBPUSD",
            "USDJPY",
            "AUDUSD",
            "USDCAD",
            "USDCHF",
            "NZDUSD",
            "EURJPY",
            "GBPJPY",
            "BTCUSD",
        )
        REQUIRED_OHLC_COLUMNS: Final[frozenset[str]] = frozenset(
            {"Open", "High", "Low", "Close", "Volume"}
        )
        TEST_TIMEFRAMES: Final[tuple[str, ...]] = ("M1", "M5", "M15", "H1", "H4", "D1")

    # =========================================================================
    # BACKWARD COMPATIBILITY ALIASES (Minimal, direct namespace access preferred)
    # =========================================================================

    # These are the ONLY aliases allowed - for frequently used constants
    # Access via direct namespace is preferred: c.MT5.GRPC_PORT,
    # c.Financial.DEFAULT_SYMBOL

    # Financial constants
    DEFAULT_SYMBOL = Financial.DEFAULT_SYMBOL
    DEFAULT_VOLUME = Financial.DEFAULT_VOLUME
    DEFAULT_BASE_PRICE = Financial.DEFAULT_BASE_PRICE

    # Database constants
    POSTGRES_DEFAULT_HOST = Database.POSTGRES_HOST
    POSTGRES_DEFAULT_PORT = Database.POSTGRES_PORT
    POSTGRES_TEST_DATABASE = Database.POSTGRES_TEST_DATABASE
    POSTGRES_TEST_USER = Database.POSTGRES_TEST_USER
    CLICKHOUSE_DEFAULT_PORT = Database.CLICKHOUSE_PORT
    MAX_CONNECTIONS_DEFAULT = Database.MAX_CONNECTIONS
    CONNECTION_TIMEOUT_DEFAULT = Database.CONNECTION_TIMEOUT
    CUSTOM_CLICKHOUSE_PORT = Database.CUSTOM_CLICKHOUSE_PORT
    CUSTOM_POSTGRES_PORT = Database.CUSTOM_POSTGRES_PORT
    CUSTOM_MAX_CONNECTIONS = Database.CUSTOM_MAX_CONNECTIONS

    # Test data constants
    DEFAULT_PERIODS = TestData.DEFAULT_PERIODS
    TEST_PERIODS_VALID = TestData.TEST_PERIODS_VALID
    INTEGRATION_PERIODS_DEFAULT = TestData.INTEGRATION_PERIODS_DEFAULT
    INVALID_HIGH_PRICE = TestData.INVALID_HIGH_PRICE
    INVALID_LOW_PRICE = TestData.INVALID_LOW_PRICE
    INVALID_CLOSE_PRICE = TestData.INVALID_CLOSE_PRICE
    TREND_UP_VALUE = TestData.TREND_UP_VALUE
    TREND_DOWN_VALUE = TestData.TREND_DOWN_VALUE
    TREND_SIDEWAYS_VALUE = TestData.TREND_SIDEWAYS_VALUE
    VOLATILITY_LOW = TestData.VOLATILITY_LOW
    VOLATILITY_MEDIUM = TestData.VOLATILITY_MEDIUM
    OHLC_INVALID_THRESHOLD = TestData.OHLC_INVALID_THRESHOLD
    PRICE_INCREMENT = TestData.PRICE_INCREMENT
    HIGH_LOW_SPREAD_SU = TestData.HIGH_LOW_SPREAD_SU
    CLOSE_ADJUSTMENT = TestData.CLOSE_ADJUSTMENT
    BASE_VOLUME_SU = TestData.BASE_VOLUME_SU
    TEST_PERIODS_EMPTY = TestData.TEST_PERIODS_EMPTY
    TEST_PERIODS_SMALL = TestData.TEST_PERIODS_SMALL
    INTEGRATION_PERIODS_SMALL = TestData.INTEGRATION_PERIODS_SMALL

    # Validation constants
    MODEL_SIZE_MIN_BYTES = Validation.MODEL_SIZE_MIN_BYTES
    TEST_TIMEOUT_SECONDS = Validation.TEST_TIMEOUT_SECONDS
    TEST_EXECUTION_TIMEOUT = Validation.TEST_EXECUTION_TIMEOUT
    STDOUT_TRUNCATE_LENGTH = Validation.STDOUT_TRUNCATE_LENGTH

    # Logging constants
    MIN_LOGGER_HANDLERS = Logging.MIN_LOGGER_HANDLERS
    MIN_LOGGER_HANDLERS_WITH_FILE = Logging.MIN_LOGGER_HANDLERS_WITH_FILE

    # Prediction constants
    CONFIDENCE_THRESHOLD_DEFAULT = Prediction.CONFIDENCE_THRESHOLD_DEFAULT
    CONFIDENCE_THRESHOLD_HIGH = Prediction.CONFIDENCE_THRESHOLD_HIGH
    CONFIDENCE_THRESHOLD_LOW = Prediction.CONFIDENCE_THRESHOLD_LOW
    CONFIDENCE_THRESHOLD_MAX = Prediction.CONFIDENCE_THRESHOLD_MAX
    CONFIDENCE_THRESHOLD_INVALID_LOW = Prediction.CONFIDENCE_THRESHOLD_INVALID_LOW
    CONFIDENCE_THRESHOLD_INVALID_HIGH = Prediction.CONFIDENCE_THRESHOLD_INVALID_HIGH

    # MT5 legacy aliases
    MT5_DEFAULT_TIMEOUT = MT5.TIMEOUT
    STARTUP_TIMEOUT = MT5.STARTUP_TIMEOUT
    GRPC_PORT = MT5.GRPC_PORT
    VNC_PORT = MT5.VNC_PORT
    HEALTH_PORT = MT5.HEALTH_PORT

    # New aliases for test infrastructure
    STARTUP_HEALTH_TIMEOUT = HealthCheck.STARTUP_TIMEOUT
    FAST_PATH_TIMEOUT = HealthCheck.FAST_PATH_TIMEOUT
    SKIP_NO_CREDENTIALS = Message.SKIP_NO_CREDENTIALS
    LOG_TAIL_LINES = TestRunner.LOG_TAIL_LINES
    LOG_TAIL_LAST_LINES = TestRunner.LOG_TAIL_LAST_LINES
    MAX_LOG_LENGTH = TestRunner.MAX_LOG_LENGTH
    CONTAINER_DIR = TestContainer.CONTAINER_DIR
    METATRADER_DIR = TestContainer.METATRADER_DIR
    DEFAULT_TIMEOUT = TestRunner.TIMEOUT
    TEST_GRPC_PORT = TestRunner.GRPC_PORT
    MIN_CONSTANTS_COUNT = Versioning.MIN_CONSTANTS_COUNT
    MIN_LOGIN_VALUE = Versioning.MIN_LOGIN_VALUE
    TMP_PATH = TestRunner.TMP_PATH
    RESTART_TEST_TOKEN_FILE = TestRunner.RESTART_TEST_TOKEN_FILE
    SUCCESS_RETURN_CODE = TestRunner.SUCCESS_RETURN_CODE
    COMMAND_TIMEOUT = TestRunner.COMMAND_TIMEOUT
    MT5_VERSION_PREFIX = VersionCheck.MT5_VERSION_PREFIX
    MAX_RANGE_RETRIES = TestRunner.MAX_RANGE_RETRIES
    VERSION_PARTS_COUNT = Versioning.VERSION_PARTS_COUNT
    REQUIRED_VERSIONS = Versioning.REQUIRED_VERSIONS

    # gRPC Service aliases
    GRPC_PORT_DEFAULT = GRPCService.PORT
    GRPC_HOST_DEFAULT = GRPCService.HOST
    GRPC_WORKERS_DEFAULT = GRPCService.WORKERS
    GRPC_CHUNK_SIZE = GRPCService.CHUNK_SIZE
    GRPC_SHUTDOWN_GRACE = GRPCService.SHUTDOWN_GRACE_PERIOD

    # Kafka aliases
    KAFKA_PORT = Kafka.PORT
    KAFKA_HOST = Kafka.HOST

    # Scripts aliases
    ALL_SCRIPTS = Scripts.ALL_SCRIPTS
    CONTAINER_MAIN_SCRIPTS = Scripts.CONTAINER_MAIN_SCRIPTS

    # Version aliases
    PYTHON_VERSION_PREFIX = VersionCheck.PYTHON_VERSION_PREFIX
    NUMPY_VERSION_PREFIX = VersionCheck.NUMPY_VERSION_PREFIX
    GRPC_VERSION_PREFIX = VersionCheck.GRPC_VERSION_PREFIX
    PYTHON_VERSION_STRING = VersionCheck.PYTHON_VERSION_STRING
    VERSION_MAJOR_MINOR_PARTS = VersionCheck.VERSION_MAJOR_MINOR_PARTS
    MIN_GRPC_MAJOR = VersionCheck.MIN_GRPC_MAJOR
    MIN_GRPC_MINOR = VersionCheck.MIN_GRPC_MINOR

    # Container aliases
    MAX_CONTAINER_RESTARTS = TestContainer.MAX_RESTARTS
    CONFIG_PATH = TestContainer.CONFIG_PATH

    # Paths aliases
    ROOT_DIR = Paths.ROOT_DIR
    TESTS_DIR = Paths.TESTS_DIR
    CONFIG_DIR = Paths.CONFIG_DIR
    S6_OVERLAY_BASE_PATH = Paths.S6_OVERLAY_BASE_PATH
    S6_RC_BASE_PATH = Paths.S6_RC_BASE_PATH
    LINUX_PYTHON_VERSION_PREFIX = Paths.LINUX_PYTHON_VERSION_PREFIX

    # File aliases
    DOCKER_COMPOSE_FILE = File.DOCKER_COMPOSE
    DOCKERIGNORE_FILE = File.DOCKERIGNORE

    # Helper method aliases
    get_project_root = staticmethod(Project.get_project_root)


# =============================================================================
# POST-CLASS INITIALIZATION - Complete Collections with enum values
# =============================================================================
# These constants depend on enums, so they're set after TestConstants is defined

TestConstants.Collections.COMPRESSION_TYPES = frozenset(
    compression.value for compression in TestConstants.Kafka.CompressionType
)
TestConstants.Collections.ACKS_MODES = frozenset(
    acks.value for acks in TestConstants.Kafka.AcksMode
)

# Add VersionPrefix alias after class is defined
TestConstants.VersionPrefix = TestConstants.VersionCheck.Prefix  # type: ignore[attr-defined]
