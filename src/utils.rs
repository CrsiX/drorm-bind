use std::fs::read_to_string;

use pyo3::prelude::*;
use rorm::{config::DatabaseConfig, Database, DatabaseConfiguration};
use serde::{Deserialize, Serialize};

use crate::common;
use crate::errors;

static DEFAULT_MAX_CONNECTIONS: u32 = 32;

#[derive(Serialize, Deserialize, Debug)]
#[serde(rename_all = "PascalCase")]
struct ConfigFile {
    database: DatabaseConfig,
}

#[pyfunction(module = "rorm_python.bindings.utils")]
fn connect_from_config(
    py: Python<'_>,
    path: String,
    min_connections: Option<u32>,
    max_connections: Option<u32>,
) -> PyResult<&PyAny> {
    let db_conf_file: ConfigFile = match toml::from_str(&read_to_string(&path)?) {
        Ok(v) => v,
        Err(err) => return Err(errors::Error::new_err(err.to_string())),
    };
    let db_conf = DatabaseConfiguration {
        driver: db_conf_file.database.driver.clone(),
        min_connections: min_connections.or_else(|| Some(1)).unwrap(),
        max_connections: max_connections
            .or_else(|| Some(DEFAULT_MAX_CONNECTIONS))
            .unwrap(),
    };
    pyo3_asyncio::tokio::future_into_py(py, async move {
        match Database::connect(db_conf).await {
            Ok(v) => Ok(common::Database { db: Box::new(v) }),
            Err(err) => Err(errors::DatabaseError::new_err(err.to_string())),
        }
    })
}

#[pymodule]
pub(super) fn utils(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(connect_from_config, m)?)?;
    Ok(())
}
