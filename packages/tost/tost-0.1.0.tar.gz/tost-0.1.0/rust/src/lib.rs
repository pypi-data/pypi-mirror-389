mod encode;
mod decode;

pub use encode::{encode, EncodeOptions};
pub use decode::decode;

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::PyObject;
use serde_json::Value;

/// Python module for TOON encoding and decoding
#[pymodule]
fn _tost(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(encode_py, m)?)?;
    m.add_function(wrap_pyfunction!(decode_py, m)?)?;
    Ok(())
}

/// Encode Python object to TOON format
#[pyfunction]
#[pyo3(signature = (obj, indent=2, delimiter=",", length_marker=None))]
fn encode_py(
    obj: Bound<'_, PyAny>,
    indent: usize,
    delimiter: &str,
    length_marker: Option<&str>,
) -> PyResult<String> {
    Python::with_gil(|_py| {
        // Convert Python object to JSON Value
        let value = convert_python_to_json(&obj)?;

        let mut options = encode::EncodeOptions::default();
        options.indent = indent;
        options.delimiter = delimiter.chars().next().unwrap_or(',');
        options.length_marker = length_marker.and_then(|s| s.chars().next());

        Ok(encode::encode(&value, &options))
    })
}

/// Decode TOON format string to Python object
#[pyfunction]
fn decode_py(toon_str: &str) -> PyResult<PyObject> {
    Python::with_gil(|py| {
        let value = decode::decode(toon_str)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))?;

        Ok(convert_json_to_python(py, &value)?.into())
    })
}

fn convert_python_to_json(obj: &Bound<'_, PyAny>) -> PyResult<Value> {
    // Handle None
    if obj.is_none() {
        return Ok(Value::Null);
    }

    // Handle bool
    if let Ok(b) = obj.extract::<bool>() {
        return Ok(Value::Bool(b));
    }

    // Handle int
    if let Ok(i) = obj.extract::<i64>() {
        return Ok(Value::Number(i.into()));
    }

    // Handle float
    if let Ok(f) = obj.extract::<f64>() {
        return Ok(Value::Number(
            serde_json::Number::from_f64(f).unwrap_or(0.into())
        ));
    }

    // Handle str
    if let Ok(s) = obj.extract::<String>() {
        return Ok(Value::String(s));
    }

    // Handle list/tuple
    if let Ok(seq) = obj.downcast::<pyo3::types::PySequence>() {
        let mut items = Vec::new();
        for item in seq.iter()? {
            items.push(convert_python_to_json(&item?)?);
        }
        return Ok(Value::Array(items));
    }

    // Handle dict
    if let Ok(dict) = obj.downcast::<pyo3::types::PyDict>() {
        let mut map = serde_json::Map::new();
        // Use keys() to preserve insertion order
        let keys = dict.keys();
        for key in keys {
            let key_str = key.extract::<String>()?;
            if let Ok(Some(value)) = dict.get_item(&key_str) {
                let json_value = convert_python_to_json(&value)?;
                map.insert(key_str, json_value);
            }
        }
        return Ok(Value::Object(map));
    }

    // Fallback: convert to string
    let s = obj.str()?.to_string();
    Ok(Value::String(s))
}

fn convert_json_to_python<'a>(py: Python<'a>, value: &Value) -> PyResult<Bound<'a, PyAny>> {
    match value {
        Value::Null => Ok(py.None().bind(py).as_any().clone()),
        Value::Bool(b) => {
            let py_bool: PyObject = (*b).into_py(py);
            Ok(py_bool.bind(py).as_any().clone())
        }
        Value::Number(n) => {
            let py_num: PyObject = if let Some(i) = n.as_i64() {
                i.into_py(py)
            } else if let Some(f) = n.as_f64() {
                f.into_py(py)
            } else {
                n.to_string().into_py(py)
            };
            Ok(py_num.bind(py).as_any().clone())
        }
        Value::String(s) => {
            let py_str: PyObject = s.into_py(py);
            Ok(py_str.bind(py).as_any().clone())
        }
        Value::Array(arr) => {
            let py_list = PyList::empty_bound(py);
            for item in arr {
                let py_item = convert_json_to_python(py, item)?;
                py_list.append(py_item)?;
            }
            Ok(py_list.as_any().clone())
        }
        Value::Object(obj) => {
            let py_dict = PyDict::new_bound(py);
            for (key, value) in obj {
                let py_value = convert_json_to_python(py, value)?;
                py_dict.set_item(key, py_value)?;
            }
            Ok(py_dict.as_any().clone())
        }
    }
}
