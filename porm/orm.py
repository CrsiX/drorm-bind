import time
import asyncio
import logging

from .ffi import *


DEFAULT_SHUTDOWN_DURATION: int = 1000  # milliseconds
MAX_CONNECTIVITY_POLLS: int = 100_000


class PyORM:
    """
    :param library: path or qualified name of the shared library (.so)
    :param options: database connectivity options
    :param logger: logger for the ORM functionalities
    :param shutdown_duration: max time in milliseconds the runtime may spend to shutdown itself
    """

    _library: ctypes.CDLL
    _logger: Optional[logging.Logger]
    _options: DBConnectOptions
    _database: Optional[Database]
    _self_pointer: ctypes.POINTER(ctypes.c_size_t)
    _shutdown_duration: ctypes.c_uint64
    _max_connectivity_iterations: int

    def __init__(
            self,
            library: str,
            options: DBConnectOptions,
            logger: Optional[logging.Logger] = None,
            shutdown_duration: int = DEFAULT_SHUTDOWN_DURATION,
            max_connectivity_polls: int = MAX_CONNECTIVITY_POLLS
    ):
        self._library = ctypes.CDLL(library)
        self._logger = logger
        self._options = options
        self._self_pointer = ctypes.pointer(ctypes.c_size_t(id(self)))
        self._shutdown_duration = ctypes.c_uint64(shutdown_duration)
        self._max_connectivity_iterations = max_connectivity_polls
        self._database = None

    async def __aenter__(self) -> "PyORM":
        """
        Start the Rust runtime and connect to the database

        :raises RuntimeError: when something went wrong starting the runtime or connecting to the database
        """

        exc: Optional[RuntimeError] = None

        global _living_orm
        if _living_orm is not None:
            raise RuntimeError("Do not spin up multiple ORM runtimes")
        _living_orm = self

        started = asyncio.Event()
        connected = asyncio.Event()

        @ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_size_t), Error)
        def runtime_start_callback(context: ctypes.POINTER(ctypes.c_size_t), error: Error):
            """
            void (*callback)(void*, struct Error)
            """

            nonlocal exc
            global _living_orm
            if _living_orm is None:
                exc = RuntimeError("Callback 'runtime_start' without living context")
            if id(_living_orm) != context.contents.value or id(_living_orm) != id(self):
                exc = RuntimeError("Callback 'runtime_start' with different context than expected")
            if error.is_error():
                exc = RuntimeError(f"Failed to start ORM runtime: {error.variant!s}: {error.message}")
            started.set()

        @ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_size_t), Database, Error)
        def db_connect_callback(context: ctypes.POINTER(ctypes.c_size_t), database: Database, error: Error):
            """
            void (*callback)(void*, Database*, struct Error)
            """

            nonlocal exc
            global _living_orm
            if _living_orm is None:
                exc = RuntimeError("Callback 'db_connect' without living context")
            if id(_living_orm) != context.contents.value or id(_living_orm) != id(self):
                exc = RuntimeError("Callback 'db_connect' with different context than expected")
            if error.is_error():
                exc = RuntimeError(f"Failed to connect to database: {error.variant!s}: {error.message}")
            else:
                self._database = database
            connected.set()

        self._library.rorm_runtime_start(runtime_start_callback, self._self_pointer)
        await started.wait()
        if exc is not None:
            self._logger and self._logger.warning("Failed to start ORM runtime")
            raise exc

        # Plainly awaiting the event will result in a deadlock
        # here, therefore sleeping shortly to fix it
        self._library.rorm_db_connect(self._options, db_connect_callback, self._self_pointer)
        iterations = 0
        while not connected.is_set():
            time.sleep(0.00001)
            iterations += 1
            if iterations >= self._max_connectivity_iterations:
                raise RuntimeError("Max number of connectivity polls reached, is the database reachable?")
        await connected.wait()

        if exc is not None:
            self._logger and self._logger.warning("Failed to connect to database")
            raise exc
        if self._database is None:
            raise RuntimeError("Connection hasn't been set up properly, the ORM callback probably delivered wrong data")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        exc: Optional[RuntimeError] = None
        closed = asyncio.Event()

        @ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_size_t), Error)
        def runtime_shutdown_callback(context: ctypes.POINTER(ctypes.c_size_t), error: Error):
            """
            void (*callback)(void*, struct Error)
            """

            nonlocal exc
            global _living_orm
            if _living_orm is None:
                exc = RuntimeError("Callback 'runtime_shutdown' without living context")
            if id(_living_orm) != context.contents.value or id(_living_orm) != id(self):
                exc = RuntimeError("Callback 'runtime_shutdown' with different context than expected")
            if error.is_error():
                exc = RuntimeError(f"Failed to shutdown ORM runtime: {error.variant!s}: {error.message}")
            closed.set()

        self._library.rorm_runtime_shutdown(self._shutdown_duration, runtime_shutdown_callback, self._self_pointer)
        await closed.wait()
        if exc is not None:
            raise exc
        global _living_orm
        _living_orm = None


_living_orm: Optional[PyORM] = None
