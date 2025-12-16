from rpyc import Service

class ThreadedServer:
    def __init__(
        self,
        service: type[Service],
        hostname: str = ...,
        port: int = ...,
        reuse_addr: bool = ...,
        protocol_config: dict[str, object] | None = ...,
    ) -> None: ...
    def start(self) -> None: ...
    def close(self) -> None: ...

class ThreadPoolServer:
    def __init__(
        self,
        service: type[Service],
        hostname: str = ...,
        port: int = ...,
        reuse_addr: bool = ...,
        nbThreads: int = ...,  # noqa: N803 - rpyc's actual parameter name
        protocol_config: dict[str, object] | None = ...,
    ) -> None: ...
    def start(self) -> None: ...
    def close(self) -> None: ...
