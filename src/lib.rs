use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::types::{PyList, PyString};
use std::borrow::Borrow;
use std::cell::UnsafeCell;
use std::collections::HashMap;
use std::ops::Deref;
use tokio::runtime;

use rorm_db;
use rorm_sql;

create_exception!(
    rorm_python,
    BindingError,
    PyException,
    "Base exception for errors originating from Rust"
);

/**
Macro to expand database queries in a match statement to handle query errors properly
*/
macro_rules! handle_db_err {
    ( $py:ident, $query:expr ) => {{
        match $query {
            Ok(value) => value.into_py($py),
            Err(e) => return Err(BindingError::new_err(e.to_string())),
        }
    }};
}

/**
Macro to convert a row of a database query result to a hashmap of column name -> Python object
*/
macro_rules! convert_row {
    ( $py:ident, $row:ident, $columns:ident ) => {{
        let mut m = HashMap::new();
        for (col, col_t) in &$columns {
            let e = match col_t {
                DatabaseValueType::Null => $py.None(),
                DatabaseValueType::String => handle_db_err!($py, $row.get::<&str, &str>(col)),
                DatabaseValueType::I64 => handle_db_err!($py, $row.get::<i64, &str>(col)),
                DatabaseValueType::I32 => handle_db_err!($py, $row.get::<i32, &str>(col)),
                DatabaseValueType::I16 => handle_db_err!($py, $row.get::<i16, &str>(col)),
                DatabaseValueType::Bool => handle_db_err!($py, $row.get::<bool, &str>(col)),
                DatabaseValueType::F64 => handle_db_err!($py, $row.get::<f64, &str>(col)),
                DatabaseValueType::F32 => handle_db_err!($py, $row.get::<f32, &str>(col)),
                DatabaseValueType::Binary => $py.None(), // TODO
                DatabaseValueType::NaiveTime => $py.None(), // TODO
                DatabaseValueType::NaiveDate => $py.None(), // TODO
                DatabaseValueType::NaiveDateTime => $py.None(), // TODO
            };
            m.insert(*col, e);
        }
        m
    }};
}

/**
Wrapper class around Rust-specific database functionality
 */
#[pyclass(module = "rorm_python.bindings")]
struct Database {
    db: Box<rorm_db::Database>,
}

#[pymethods(module = "rorm_python.bindings")]
impl Database {
    /// Get the columns of all rows of a table synchronously
    fn query_all_sync<'p>(
        self_: PyRef<Self>,
        py: Python<'p>,
        table: String,
        columns: Vec<(&str, DatabaseValueType)>,
    ) -> PyResult<&'p PyList> {
        let db: &rorm_db::Database = self_.db.as_ref();
        let cols: Vec<&str> = columns.iter().map(|e| e.0).collect();
        let mut results: Vec<HashMap<&str, PyObject>> = Vec::new();
        let result = pyo3_asyncio::tokio::get_runtime().block_on(async {
            return db.query_all(table.as_str(), cols.as_slice(), None).await;
        });

        match result {
            Ok(rows) => {
                for i in 0..rows.len() {
                    let row: &rorm_db::row::Row = &rows[i];
                    results.push(convert_row!(py, row, columns));
                }
            }
            Err(e) => return Err(BindingError::new_err(e.to_string())),
        };
        return Ok(PyList::new(py, results));
    }

    /// Delete all rows of a table synchronously
    fn delete_all_sync(self_: PyRef<Self>, table: String) -> PyResult<bool> {
        let db: &rorm_db::Database = self_.db.as_ref();
        pyo3_asyncio::tokio::get_runtime().block_on(async {
            return match db.delete(table.as_str(), None).await {
                Ok(v) => Ok(true),
                Err(v) => Err(BindingError::new_err(v.to_string())),
            };
        })
    }
}

#[pyfunction(module = "rorm_python.bindings")]
fn connect_sqlite_database(
    py: Python<'_>,
    filename: String,
    min_connections: u32,
    max_connections: u32,
) -> PyResult<&PyAny> {
    let conf = rorm_db::DatabaseConfiguration {
        backend: rorm_db::DatabaseBackend::SQLite,
        name: filename,
        host: "".to_string(),
        port: 0,
        user: "".to_string(),
        password: "".to_string(),
        min_connections,
        max_connections,
    };
    pyo3_asyncio::tokio::future_into_py(py, async {
        let r = rorm_db::Database::connect(conf).await;
        return match r {
            Ok(v) => Ok(Database { db: Box::new(v) }),
            Err(v) => Err(BindingError::new_err(v.to_string())),
        };
    })
}

/**
Enum of the different database row types
*/
#[pyclass]
#[derive(Copy, Clone, Debug, PartialEq)]
enum DatabaseValueType {
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
Direct Python bindings for RORM, the Rust ORM

Those bindings provide very convenient features to the Python runtime,
but they should not be used by application directly. Use the wrapped
functions and classes of the outer package in application code instead,
especially since those bindings are less documented and may change
their behavior or API without explicit notice between versions.
 */
#[pymodule]
fn bindings(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add("BindingError", _py.get_type::<BindingError>())?;
    m.add_function(wrap_pyfunction!(connect_sqlite_database, m)?)?;
    m.add_class::<Database>()?;
    m.add_class::<DatabaseValueType>()?;
    Ok(())
}
