import ctypes
from typing import Callable, List, Optional, Type, Union

from .ffi_enums import *


Row = ctypes.POINTER(ctypes.c_size_t)  # real type signature unknown
Stream = ctypes.POINTER(ctypes.c_size_t)  # real type signature unknown
Database = ctypes.POINTER(ctypes.c_size_t)  # real type signature unknown

_CData = ctypes.Structure.mro()[1]


def make_slice(
        cls_name: str,
        referenced_type: _CData,
        docstring: str,
        repr_: Optional[Callable[[], str]] = None,
        str_: Optional[Callable[[], str]] = None,
        new: Optional[Callable] = None,
        extras: Optional[dict] = None
) -> type:
    def __repr__(self: cls_name) -> str:
        return f"<{type(self).__name__}[{', '.join([str(v.size) for v in self.to_list()])}]>"

    def __str__(self: cls_name) -> str:
        return f"[{', '.join(map(str, self.to_list()))}]"

    def to_list(self) -> List[referenced_type]:
        result = []
        if self.size == 0:
            return result
        for i, v in enumerate(self.content):
            if i >= self.size:
                break
            result.append(v)
        return result

    kwargs = {
        "__doc__": docstring,
        "__repr__": repr_ or __repr__,
        "__str__": str_ or __str__,
        "_fields_": [
            ("content", ctypes.POINTER(referenced_type)),
            ("size", ctypes.c_size_t)
        ],
        "to_list": to_list
    }
    if new is not None:
        kwargs["new"] = classmethod(new)
    kwargs.update(extras or {})
    return type(cls_name, (ctypes.Structure,), kwargs)


def _make_string() -> Type["FFIString"]:
    def new(_, v: Union[str, bytes]) -> "FFIString":
        if isinstance(v, str):
            v = v.encode("UTF-8")
        elif not isinstance(v, bytes):
            raise TypeError(f"Wrong type {type(v)}, expected str or bytes")
        t = ctypes.c_uint8 * len(v)
        return FFIString(t(*v), len(v))

    def __str__(self) -> str:
        return self.to_bytes().decode("UTF-8")

    def __repr__(self) -> str:
        return f"<FFIString({self.size})>"

    def to_bytes(self) -> bytes:
        if self.size == 0:
            return b""
        data = bytearray()
        for i, v in enumerate(self.content):
            if i >= self.size:
                break
            data.append(v)
        return bytes(data)

    return make_slice(
        "FFIString",
        ctypes.c_uint8,
        """
        typedef struct FFIString {
          const uint8_t *content;
          size_t size;
        } FFIString;
        """,
        __repr__,
        __str__,
        new,
        {"to_bytes": to_bytes}
    )


def _ffi_string_slice_new(_, v: Union[List[str], List[bytes]]) -> "FFIStringSlice":
    if not isinstance(v, list):
        raise TypeError(f"Expected type list, not {type(v)}")
    slices = [FFIString.new(i) for i in v]
    t = FFIString * len(slices)
    return FFIStringSlice(t(*slices), len(slices))


_ffi_string_slice_new.__name__ = "new"
FFIString = _make_string()
FFIStringSlice = make_slice(
    "FFIStringSlice",
    FFIString,
    """
    typedef struct FFISlice_FFIString {
      const struct FFIString *content;
      size_t size;
    } FFISlice_FFIString;
    """,
    new=_ffi_string_slice_new
)


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
