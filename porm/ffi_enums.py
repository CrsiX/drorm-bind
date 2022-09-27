import enum


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
    TERNARY_CONDITION = 4
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


class TernaryConditionTag(enum.IntEnum):
    """
    typedef int_t TernaryConditionTag;
    """

    BETWEEN = 0
    NOT_BETWEEN = 1


class ValueTag(enum.IntEnum):
    """
    typedef int_t ValueTag;
    """

    NULL = 0
    IDENT = 1
    """Representation of an identifier, e.g. column. This value will not be escaped! Don't pass unchecked data to it!"""
    STRING = 2
    I64 = 3
    I32 = 4
    I16 = 5
    BOOL = 6
    F64 = 7
    F32 = 8
    BINARY = 9


class OptionTag(enum.IntEnum):
    """
    typedef int_t OptionTag;
    """

    NONE = 0
    SOME = 1
