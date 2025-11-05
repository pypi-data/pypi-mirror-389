use pyo3::prelude::*;
use ::bip322 as bip322_rs;

#[pyfunction(
    text_signature = "(address, message, base64_signature)",
    signature = (address, message, base64_signature)
)]
#[pyo3(name = "verify_simple_encoded")]
#[doc = "Verify a base64-encoded BIP-322 signature.\n\n\
           Args:\n  address (str): Bitcoin address\n  \
                 message (str): message text\n  \
                 base64_signature (str): base64 signature\n\n\
           Returns:\n  bool: True if valid, else False"]
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
