use pyo3::prelude::*;

#[pymodule]
pub(super) fn postgres(_py: Python, m: &PyModule) -> PyResult<()> {
    let _m = m;
    Ok(())
}
