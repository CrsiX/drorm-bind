use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::types::PyList;
use std::collections::HashMap;

use rorm::{config::DatabaseConfig, Database, DatabaseConfiguration, DatabaseDriver};

mod common;
mod errors;
mod macros;
mod sqlite;

/**
Direct Python bindings for RORM, the Rust ORM

This package is an implementation of the Python DB API Specification v2.0.
 */
#[pymodule]
fn bindings(_py: Python, m: &PyModule) -> PyResult<()> {
    // Error classes required by Database API Spec 2.0
    let mod_err = PyModule::new(_py, "errors")?;
    mod_err.add("Error", _py.get_type::<errors::Error>())?;
    mod_err.add("Warning", _py.get_type::<errors::Warning>())?;
    mod_err.add("InterfaceError", _py.get_type::<errors::InterfaceError>())?;
    mod_err.add("DatabaseError", _py.get_type::<errors::DatabaseError>())?;
    mod_err.add("DataError", _py.get_type::<errors::DataError>())?;
    mod_err.add(
        "OperationalError",
        _py.get_type::<errors::OperationalError>(),
    )?;
    mod_err.add("IntegrityError", _py.get_type::<errors::IntegrityError>())?;
    mod_err.add("InternalError", _py.get_type::<errors::InternalError>())?;
    mod_err.add("InterfaceError", _py.get_type::<errors::ProgrammingError>())?;
    mod_err.add(
        "InterfaceError",
        _py.get_type::<errors::NotSupportedError>(),
    )?;
    m.add_submodule(mod_err);

    // MySQL-specific implementation details

    // Postgres-specific implementation details

    // SQLite-specific implementation details
    let mod_sqlite = PyModule::new(_py, "sqlite")?;
    sqlite::sqlite(_py, mod_sqlite);
    m.add_submodule(mod_sqlite);

    // Generic, non-specific features
    m.add_class::<common::Database>()?;
    m.add_class::<common::DatabaseValueType>()?;

    Ok(())
}
