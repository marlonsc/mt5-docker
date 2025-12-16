"""Type stubs for python-dotenv."""

from pathlib import Path

def load_dotenv(
    dotenv_path: str | Path | None = ...,
    stream: object | None = ...,
    verbose: bool = ...,
    override: bool = ...,
    interpolate: bool = ...,
    encoding: str | None = ...,
) -> bool: ...
