use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use rorm::{config::DatabaseConfig, Database as DB, DatabaseConfiguration, DatabaseDriver};

use crate::common;
use crate::errors;

#[pyfunction(module = "rorm_python.bindings.sqlite")]
fn connect(
    py: Python<'_>,
    filename: String,
    min_connections: u32,
    max_connections: u32,
) -> PyResult<&PyAny> {
    pyo3_asyncio::tokio::future_into_py(py, async move {
        match DB::connect(DatabaseConfiguration {
            driver: DatabaseDriver::SQLite { filename },
            min_connections,
            max_connections,
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
