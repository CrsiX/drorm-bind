use pyo3::create_exception;
use pyo3::exceptions::PyException;

create_exception!(
    rorm_python,
    Error,
    PyException,
    "Exception for errors originating from the Rust ORM"
);

create_exception!(
    rorm_python,
    Warning,
    PyException,
    "Exception raised for important warnings like data truncations while inserting"
);

create_exception!(
    rorm_python,
    InterfaceError,
    Error,
    "Exception raised for misuse of the low-level database C API"
);

create_exception!(
    rorm_python,
    DatabaseError,
    Error,
    "Exception raised for errors related to the database usage"
);

create_exception!(
    rorm_python,
    DataError,
    DatabaseError,
    "Exception raised for errors that are due to problems with the processed data like division by zero, numeric value out of range"
);

create_exception!(
    rorm_python,
    OperationalError,
    DatabaseError,
    "Exception raised for errors that are related to the database’s operation and not necessarily under the control of the programmer"
);

create_exception!(
    rorm_python,
    IntegrityError,
    DatabaseError,
    "Exception raised when the relational integrity of the database is affected, e.g. a foreign key check fails"
);

create_exception!(
    rorm_python,
    InternalError,
    DatabaseError,
    "Exception raised when the database encounters an internal error, e.g. the cursor is not valid anymore, the transaction is out of sync"
);

create_exception!(
    rorm_python,
    ProgrammingError,
    DatabaseError,
    "Exception raised for programming errors, e.g. table not found or already exists, syntax error in the SQL statement, wrong number of parameters specified"
);

create_exception!(
    rorm_python,
    NotSupportedError,
    DatabaseError,
    "Exception raised in case a method or database API was used which is not supported by the database, e.g. requesting a .rollback() on a connection that does not support transaction or has transactions turned off"
);
