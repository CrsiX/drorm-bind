import enum
import ctypes
from typing import List, Optional, Union


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


class ConditionTag(enum.IntEnum):
    """
    typedef int_t ConditionTag;
    """

    CONJUNCTION = 0
    DISJUNCTION = 1
    UNARY_CONDITION = 2
    BINARY_CONDITION = 3
    TERTIARY_CONDITION = 4
    VALUE = 5


class UnaryConditionTag(enum.IntEnum):
    """
    typedef int_t UnaryConditionTag;
    """

    IS_NULL = 0
    IS_NOT_NULL = 1
    EXISTS = 2
    NOT_EXISTS = 3
    NOT = 4


class BinaryConditionTag(enum.IntEnum):
    """
    typedef int_t BinaryConditionTag;
    """

    EQUALS = 0
    NOT_EQUALS = 1
    GREATER = 2
    GREATER_OR_EQUALS = 3
    LESS = 4
    LESS_OR_EQUALS = 5
    LIKE = 6
    NOT_LIKE = 7
    REGEXP = 8
    NOT_REGEXP = 9
    IN = 10
    NOT_IN = 11


class TertiaryConditionTag(enum.IntEnum):
    """
    typedef int_t TertiaryConditionTag;
    """

    BETWEEN = 0
    NOT_BETWEEN = 1


class ValueTag(enum.IntEnum):
    """
    typedef int_t ValueTag;
    """

    IDENT = 0
    STRING = 1
    I64 = 2
    I32 = 3
    I16 = 4
    BOOL = 5
    F64 = 6
    F32 = 7
    NULL = 8


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


class FFIStringSlice(ctypes.Structure):
    """
    typedef struct FFISlice_FFIString {
      const struct FFIString *content;
      size_t size;
    } FFISlice_FFIString;
    """

    _fields_ = [
        ("content", ctypes.POINTER(FFIString)),
        ("size", ctypes.c_size_t)
    ]

    @classmethod
    def new(cls, v: Union[List[str], List[bytes]]) -> "FFIStringSlice":
        if not isinstance(v, list):
            raise TypeError(f"Expected type list, not {type(v)}")
        if not all([isinstance(i, str) for i in v]) and not all([isinstance(i, bytes) for i in v]):
            raise TypeError("Expected list of str or list of bytes")
        slices = [FFIString.new(i) for i in v]
        t = FFIString * len(slices)
        return FFIStringSlice(t(*slices), len(slices))

    def to_list(self) -> List[FFIString]:
        result = []
        if self.size == 0:
            return result
        for i, v in enumerate(self.content):
            if i >= self.size:
                break
            result.append(v)
        return result

    def __str__(self) -> str:
        return f"[{', '.join(map(str, self.to_list()))}]"

    def __repr__(self) -> str:
        return f"<FFIStringSlice[{', '.join([str(v.size) for v in self.to_list()])}]>"


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
