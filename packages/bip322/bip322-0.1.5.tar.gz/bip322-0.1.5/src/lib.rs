use pyo3::prelude::*;
use ::bip322 as bip322_rs;

#[pyfunction]
fn verify_simple_encoded(address: &str, message: &str, base64_signature: &str) -> PyResult<bool> {
    match bip322_rs::verify_simple_encoded(address, message, base64_signature) {
        Ok(()) => Ok(true),
        Err(_e) => Ok(false),
    }
}

#[pymodule]
#[pyo3(name = "bip322")]  // Python import name: `import bip322`
fn bip322_py(_py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(verify_simple_encoded, m)?)?;
    Ok(())
}
