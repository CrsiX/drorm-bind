use pyo3::prelude::*;
use rorm::{Database, DatabaseConfiguration, DatabaseDriver};

use crate::common;
use crate::errors;

static DEFAULT_MAX_CONNECTIONS: u32 = 16;

#[pyfunction(module = "rorm_python.bindings.sqlite")]
fn connect(
    py: Python<'_>,
    filename: String,
    min_connections: Option<u32>,
    max_connections: Option<u32>,
) -> PyResult<&PyAny> {
    pyo3_asyncio::tokio::future_into_py(py, async move {
        match Database::connect(DatabaseConfiguration {
            driver: DatabaseDriver::SQLite { filename },
            min_connections: min_connections.or_else(|| Some(1)).unwrap(),
            max_connections: max_connections
                .or_else(|| Some(DEFAULT_MAX_CONNECTIONS))
                .unwrap(),
        })
        .await
        {
            Ok(v) => Ok(common::Database { db: Box::new(v) }),
            Err(err) => Err(errors::DatabaseError::new_err(err.to_string())),
        }
    })
}

#[pymodule]
pub(super) fn sqlite(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(connect, m)?)?;
    Ok(())
}
