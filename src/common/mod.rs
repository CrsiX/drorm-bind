use pyo3::prelude::*;

use rorm;

/**
Enum of the different database row types
 */
#[pyclass]
#[derive(Copy, Clone, Debug, PartialEq)]
pub(crate) enum DatabaseValueType {
    Null,
    String,
    I64,
    I32,
    I16,
    Bool,
    F64,
    F32,
    Binary,
    NaiveTime,
    NaiveDate,
    NaiveDateTime,
}

/**
Wrapper class around Rust-specific database functionality
 */
#[pyclass(module = "rorm_python")]
pub(crate) struct Database {
    pub(crate) db: Box<rorm::Database>,
}
