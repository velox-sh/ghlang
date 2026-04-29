// docstrings here target Python hover, not rustdoc
#![allow(clippy::doc_markdown)]

use pyo3::prelude::*;

const PACKAGE_VERSION: &str = "3.0.0-dev";

#[pyfunction]
fn version() -> &'static str {
    PACKAGE_VERSION
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add("__version__", PACKAGE_VERSION)?;
    Ok(())
}
