use pyo3::prelude::*;
use rorm::{Database, DatabaseConfiguration, DatabaseDriver};

use crate::common;
use crate::errors;

static DEFAULT_HOST: &str = "localhost";
static DEFAULT_PORT: u16 = 3306;
static DEFAULT_MAX_CONNECTIONS: u32 = 32;

#[pyfunction(module = "rorm_python.bindings.mysql")]
fn connect(
    py: Python<'_>,
    database: String,
    user: String,
    password: String,
    host: Option<String>,
    port: Option<u16>,
    min_connections: Option<u32>,
    max_connections: Option<u32>,
) -> PyResult<&PyAny> {
    pyo3_asyncio::tokio::future_into_py(py, async move {
        match Database::connect(DatabaseConfiguration {
            driver: DatabaseDriver::MySQL {
                name: database,
                host: host.or_else(|| Some(DEFAULT_HOST.to_string())).unwrap(),
                port: port.or_else(|| Some(DEFAULT_PORT)).unwrap(),
                user,
                password,
            },
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
pub(super) fn mysql(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(connect, m)?)?;
    Ok(())
}
