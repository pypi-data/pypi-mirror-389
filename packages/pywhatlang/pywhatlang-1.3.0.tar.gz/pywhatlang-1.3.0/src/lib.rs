use pyo3::prelude::*;
use whatlang::detect;


/// Detect the language of a given string of text.
#[pyfunction]
fn detect_lang(text: String) -> PyResult<(String, f64, bool)> {
    let info = detect(&text).unwrap();
    Ok((info.lang().code().to_string(), info.confidence(), info.is_reliable()))
}

/// A wrapper for whatlang rust crate.
#[pymodule]
fn pywhatlang(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(detect_lang, m)?)?;
    Ok(())
}