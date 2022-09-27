import time
import asyncio
import logging

from .ffi import *
from . import _utils


DEFAULT_SHUTDOWN_DURATION: int = 1000  # milliseconds
CONNECTIVITY_TIMEOUT: float = 10  # seconds


class PyORM:
    """
    :param library: path or qualified name of the shared library (.so)
    :param options: database connectivity options
    :param logger: logger for the ORM functionalities
    :param shutdown_duration: max time in milliseconds the runtime may spend to shutdown itself
    """

    _available: bool
    _library: ctypes.CDLL
    _logger: Optional[logging.Logger]
    _options: DBConnectOptions
    _database: Optional[Database]
    _self_pointer: ctypes.POINTER(ctypes.c_size_t)
    _shutdown_duration: ctypes.c_uint64
    _connectivity_timeout: float

    def __init__(
            self,
            library: str,
            options: DBConnectOptions,
            logger: Optional[logging.Logger] = None,
            shutdown_duration: int = DEFAULT_SHUTDOWN_DURATION,
            connectivity_timeout: float = CONNECTIVITY_TIMEOUT
    ):
        self._available = False
        self._library = ctypes.CDLL(library)
        self._logger = logger
        self._options = options
        self._database = None
        self._self_pointer = ctypes.pointer(ctypes.c_size_t(id(self)))
        self._shutdown_duration = ctypes.c_uint64(shutdown_duration)
        self._connectivity_timeout = connectivity_timeout

    def __check(self, callback_name: str, context: ContextType) -> Optional[RuntimeError]:
        """
        Check the environment settings and supplied pointers for validity

        :param callback_name: name of the callback function that executes this checker
        :param context: reference to a self pointer
        :return: optional RuntimeError when pointers are invalid or the living ORM value changed
        """

        if _living_orm is None:
            return RuntimeError(f"Callback {callback_name!r} without living context")
        if _utils.is_null_ptr(context):
            return RuntimeError("Supplied context pointer is a NULL pointer")
        if id(_living_orm) != context.contents.value or id(_living_orm) != id(self):
            return RuntimeError(f"Callback {callback_name!r} with different context than expected")

    async def __aenter__(self) -> "PyORM":
        """
        Start the ORM runtime and connect to the database

        :raises RuntimeError: when something went wrong starting the runtime or connecting to the database
        """

        exc: Optional[RuntimeError] = None

        global _living_orm
        if _living_orm is not None:
            raise RuntimeError("Do not spin up multiple ORM runtimes")
        _living_orm = self

        started = asyncio.Event()
        connected = asyncio.Event()

        @ctypes.CFUNCTYPE(None, ContextType, Error)
        def runtime_start_callback(context: ContextType, error: Error):
            """
            void (*callback)(void*, struct Error)
            """

            nonlocal exc
            exc = self.__check("runtime_start_callback", context)
            if exc is None and error.is_error():
                exc = RuntimeError(f"Failed to start ORM runtime: {error.variant!s}: {error.message}")
            started.set()

        @ctypes.CFUNCTYPE(None, ContextType, Database, Error)
        def db_connect_callback(context: ContextType, database: Database, error: Error):
            """
            void (*callback)(void*, Database*, struct Error)
            """

            nonlocal exc
            exc = self.__check("db_connect_callback", context)
            if exc is None and error.is_error():
                self._logger and self._logger.warning(f"Failed to connect to database: {error.message}")
                exc = RuntimeError(f"Failed to connect to database: {error.variant!s}: {error.message}")
            else:
                self._database = database
            connected.set()

        self._library.rorm_runtime_start(runtime_start_callback, self._self_pointer)
        await started.wait()
        if exc is not None:
            self._logger and self._logger.warning("Failed to start ORM runtime")
            raise exc
        self._logger and self._logger.debug("Started ORM runtime")

        # Plainly awaiting the event will result in a deadlock
        # here, therefore sleeping shortly to fix it
        self._library.rorm_db_connect(self._options, db_connect_callback, self._self_pointer)
        start = time.time()
        while not connected.is_set():
            time.sleep(0.0001)
            if (time.time() - start) >= self._connectivity_timeout:
                raise RuntimeError("Connectivity timeout reached, is the database reachable?")
        await connected.wait()

        if exc is not None:
            self._logger and self._logger.warning("Failed to connect to database")
            raise exc
        if self._database is None:
            raise RuntimeError("Connection hasn't been set up properly, the ORM callback probably delivered wrong data")

        self._available = True
        self._logger and self._logger.debug(f"Connected to database in {time.time() - start:.3f}s")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Close the database connection, clean up and shutdown the ORM runtime

        :raises RuntimeError: when shutting down the ORM runtime failed
        """

        exc: Optional[RuntimeError] = None
        closed = asyncio.Event()

        if self._database is None:
            self._logger and self._logger.debug("Can't close database connection, database hasn't been set up properly")
        else:
            self._library.rorm_db_free(self._database)
            self._logger and self._logger.debug("Closed database connection")

        @ctypes.CFUNCTYPE(None, ContextType, Error)
        def runtime_shutdown_callback(context: ContextType, error: Error):
            """
            void (*callback)(void*, struct Error)
            """

            nonlocal exc
            exc = self.__check("db_connect_callback", context)
            if exc is None and error.is_error():
                exc = RuntimeError(f"Failed to shutdown ORM runtime: {error.variant!s}: {error.message}")
            closed.set()

        self._library.rorm_runtime_shutdown(self._shutdown_duration, runtime_shutdown_callback, self._self_pointer)
        await closed.wait()

        self._available = False
        self._logger and self._logger.debug("Closed ORM runtime")
        if exc is not None:
            raise exc
        global _living_orm
        _living_orm = None


_living_orm: Optional[PyORM] = None
