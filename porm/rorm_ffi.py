import enum
import ctypes
from typing import Optional, Union


Row = ctypes.POINTER(ctypes.c_size_t)  # real type signature unknown
Stream = ctypes.POINTER(ctypes.c_size_t)  # real type signature unknown
Database = ctypes.POINTER(ctypes.c_size_t)  # real type signature unknown


class DBBackend(enum.IntEnum):
    """
    typedef int32_t DBBackend;
    """

    INVALID = 0
    SQLITE = 1
    MYSQL = 2
    POSTGRES = 3


class ErrorTag(enum.IntEnum):
    """
    typedef int_t ErrorTag;
    """

    NO_ERROR = 0
    MISSING_RUNTIME_ERROR = 1
    RUNTIME_ERROR = 2
    INVALID_STRING_ERROR = 3
    CONFIGURATION_ERROR = 4
    DATABASE_ERROR = 5
    NO_ROWS_LEFT_IN_STREAM = 6
    COLUMN_DECODE_ERROR = 7
    COLUMN_NOT_FOUND_ERROR = 8
    COLUMN_INDEX_OUT_OF_BOUNDS = 9


class FFIString(ctypes.Structure):
    """
    typedef struct FFIString {
      const uint8_t *content;
      size_t size;
    } FFIString;
    """

    _fields_ = [
        ("content", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t)
    ]

    @classmethod
    def new(cls, v: Union[str, bytes]) -> "FFIString":
        if isinstance(v, str):
            v = v.encode("UTF-8")
        elif not isinstance(v, bytes):
            raise TypeError(f"Wrong type {type(v)}")
        t = ctypes.c_uint8 * len(v)
        return FFIString(t(*v), len(v))

    def to_bytes(self) -> bytes:
        if self.size == 0:
            return b""
        data = bytearray()
        for i, v in enumerate(self.content):
            if i >= self.size:
                break
            data.append(v)
        return bytes(data)

    def __str__(self) -> str:
        return self.to_bytes().decode("UTF-8")

    def __repr__(self) -> str:
        return f"<FFIString({self.size})>"


class Error(ctypes.Structure):
    """
    typedef struct Error {
      Error_Tag tag;
      struct FFIString error;
    } Error;
    """

    _fields_ = [
        ("tag", ctypes.c_int),
        ("error", FFIString)
    ]

    _available_messages_ = (ErrorTag.RUNTIME_ERROR, ErrorTag.CONFIGURATION_ERROR, ErrorTag.DATABASE_ERROR)

    @property
    def message(self) -> Optional[FFIString]:
        if ErrorTag(self.tag) in self._available_messages_:
            return self.error
        return None

    @property
    def variant(self) -> ErrorTag:
        return ErrorTag(self.tag)

    def is_error(self) -> bool:
        return ErrorTag(self.tag) != ErrorTag.NO_ERROR


class DBConnectOptions(ctypes.Structure):
    """
    typedef struct DBConnectOptions {
      DBBackend backend;
      struct FFIString name;
      struct FFIString host;
      uint16_t port;
      struct FFIString user;
      struct FFIString password;
      uint32_t min_connections;
      uint32_t max_connections;
    } DBConnectOptions;
    """

    _fields_ = [
        ("backend", ctypes.c_int32),
        ("name", FFIString),
        ("host", FFIString),
        ("port", ctypes.c_uint16),
        ("user", FFIString),
        ("password", FFIString),
        ("min_connections", ctypes.c_uint32),
        ("max_connections", ctypes.c_uint32)
    ]

    @classmethod
    def new(
            cls,
            backend: DBBackend,
            name: str,
            host: str,
            port: int,
            user: str,
            password: str,
            min_connections: int = 1,
            max_connections: int = 32
    ) -> "DBConnectOptions":
        if not 0 < port < 65536:
            raise ValueError("'port' out of range")
        if not 0 < min_connections < 2 ** 32:
            raise ValueError("'min_connections' out of range")
        if not 0 < max_connections < 2 ** 32:
            raise ValueError("'max_connections' out of range")
        return DBConnectOptions(
            ctypes.c_int32(int(backend.value)),
            FFIString.new(name),
            FFIString.new(host),
            ctypes.c_uint16(port),
            FFIString.new(user),
            FFIString.new(password),
            ctypes.c_uint32(min_connections),
            ctypes.c_uint32(max_connections)
        )
