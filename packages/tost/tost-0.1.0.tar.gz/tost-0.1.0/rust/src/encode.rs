use serde_json::Value;

#[derive(Debug, Clone)]
pub struct EncodeOptions {
    pub indent: usize,
    pub delimiter: char,
    pub length_marker: Option<char>,
}

impl Default for EncodeOptions {
    fn default() -> Self {
        EncodeOptions {
            indent: 2,
            delimiter: ',',
            length_marker: None,
        }
    }
}

pub fn encode(value: &Value, options: &EncodeOptions) -> String {
    let mut result = String::new();
    encode_value(value, options, 0, None, &mut result);
    result
}

fn encode_value(value: &Value, options: &EncodeOptions, level: usize, key: Option<&str>, output: &mut String) {
    match value {
        Value::Null => {
            output.push_str("null");
        }
        Value::Bool(b) => {
            output.push_str(if *b { "true" } else { "false" });
        }
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                output.push_str(&i.to_string());
            } else if let Some(f) = n.as_f64() {
                let s = f.to_string();
                // Remove trailing zeros
                let trimmed = s.trim_end_matches('0').trim_end_matches('.');
                output.push_str(trimmed);
            } else {
                output.push_str(&n.to_string());
            }
        }
        Value::String(s) => {
            output.push_str(&quote_string(s, options.delimiter));
        }
        Value::Array(arr) => {
            encode_array(arr, options, level, key, output);
        }
        Value::Object(obj) => {
            encode_object(obj, options, level, output);
        }
    }
}

fn encode_array(arr: &[Value], options: &EncodeOptions, level: usize, key: Option<&str>, output: &mut String) {
    if arr.is_empty() {
        let indent_str = " ".repeat(level * options.indent);
        let mut len_str = if let Some(marker) = options.length_marker {
            format!("{}{}", marker, 0)
        } else {
            "0".to_string()
        };
        if options.delimiter != ',' {
            len_str.push(options.delimiter);
        }
        output.push_str(&indent_str);
        match key {
            Some(k) => {
                output.push_str(&format!("{}[{}]:", k, len_str));
            }
            None => {
                output.push_str(&format!("[{}]:", len_str));
            }
        }
        return;
    }
    
    // Check if all elements are objects with the same keys (tabular format)
    if let Some(keys) = check_tabular_format(arr) {
        encode_tabular_array(arr, keys, options, level, key, output);
        return;
    }

    // Check if all elements are primitives (inline format)
    if arr.iter().all(|v| is_primitive(v)) {
        encode_inline_array(arr, options, level, key, output);
        return;
    }

    // Check if all elements are arrays (array of arrays)
    if arr.iter().all(|v| matches!(v, Value::Array(_))) {
        encode_array_of_arrays(arr, options, level, key, output);
        return;
    }

    // List format (mixed or non-uniform)
    encode_list_array(arr, options, level, key, output);
}

fn check_tabular_format(arr: &[Value]) -> Option<Vec<String>> {
    if arr.is_empty() {
        return None;
    }

    let first_obj = match arr.first() {
        Some(Value::Object(obj)) => obj,
        _ => return None,
    };

    // Get keys from first object (preserve original order)
    let keys: Vec<String> = first_obj.keys().cloned().collect();

    // Check if all objects have the same keys and all values are primitives
    for item in arr {
        let obj = match item {
            Value::Object(o) => o,
            _ => return None,
        };

        // Same set of keys (order may differ)
        if obj.len() != keys.len() || !keys.iter().all(|k| obj.contains_key(k)) {
            return None;
        }

        // Check if all values are primitives
        for key in &keys {
            if let Some(val) = obj.get(key) {
                if !is_primitive(val) {
                    return None;
                }
            }
        }
    }

    Some(keys)
}

fn encode_tabular_array(
    arr: &[Value],
    keys: Vec<String>,
    options: &EncodeOptions,
    level: usize,
    key: Option<&str>,
    output: &mut String,
) {
    let indent_str = " ".repeat(level * options.indent);
    let mut len_str = if let Some(marker) = options.length_marker {
        format!("{}{}", marker, arr.len())
    } else {
        arr.len().to_string()
    };
    if options.delimiter != ',' {
        len_str.push(options.delimiter);
    }

    // Header: (key|)[length]{key1<delim>key2...}:
    output.push_str(&indent_str);
    let delim_s = options.delimiter.to_string();
    let fields_join = keys.join(&delim_s);
    match key {
        Some(k) => {
            output.push_str(&format!("{}[{}]{{{}}}:", k, len_str, fields_join));
        }
        None => {
            // Root-level array header without a key
            output.push_str(&format!("[{}]{{{}}}:", len_str, fields_join));
        }
    }
    output.push('\n');

    // Rows
    for item in arr {
        let obj = match item {
            Value::Object(o) => o,
            _ => continue,
        };

        output.push_str(&indent_str);
        output.push_str("  ");

        let mut first = true;
        for key in &keys {
            if !first {
                output.push(options.delimiter);
            }
            first = false;

            if let Some(val) = obj.get(key) {
                encode_tabular_value(val, options, output);
            }
        }
        output.push('\n');
    }
}

fn encode_tabular_value(value: &Value, options: &EncodeOptions, output: &mut String) {
    match value {
        Value::String(s) => {
            output.push_str(&quote_string(s, options.delimiter));
        }
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                output.push_str(&i.to_string());
            } else if let Some(f) = n.as_f64() {
                let s = f.to_string();
                let trimmed = s.trim_end_matches('0').trim_end_matches('.');
                output.push_str(trimmed);
            } else {
                output.push_str(&n.to_string());
            }
        }
        Value::Bool(b) => {
            output.push_str(if *b { "true" } else { "false" });
        }
        Value::Null => {
            output.push_str("null");
        }
        _ => {}
    }
}

fn encode_inline_array(arr: &[Value], options: &EncodeOptions, level: usize, key: Option<&str>, output: &mut String) {
    let indent_str = " ".repeat(level * options.indent);
    let mut len_str = if let Some(marker) = options.length_marker {
        format!("{}{}", marker, arr.len())
    } else {
        arr.len().to_string()
    };
    if options.delimiter != ',' {
        len_str.push(options.delimiter);
    }

    if let Some(k) = key {
        output.push_str(&indent_str);
        output.push_str(&format!("{}[{}]:", k, len_str));
    } else {
        output.push_str(&format!("[{}]:", len_str));
    }

    let mut first = true;
    for item in arr {
        if !first {
            output.push(options.delimiter);
        }
        first = false;

        match item {
            Value::String(s) => {
                output.push_str(&quote_string(s, options.delimiter));
            }
            _ => {
                encode_value(item, options, 0, None, output);
            }
        }
    }
}

fn encode_array_of_arrays(
    arr: &[Value],
    options: &EncodeOptions,
    level: usize,
    key: Option<&str>,
    output: &mut String,
) {
    let indent_str = " ".repeat(level * options.indent);
    let mut len_str = if let Some(marker) = options.length_marker {
        format!("{}{}", marker, arr.len())
    } else {
        arr.len().to_string()
    };
    if options.delimiter != ',' {
        len_str.push(options.delimiter);
    }

    output.push_str(&indent_str);
    match key {
        Some(k) => output.push_str(&format!("{}[{}]:", k, len_str)),
        None => output.push_str(&format!("[{}]:", len_str)),
    }
    output.push('\n');

    for item in arr {
        if let Value::Array(sub_arr) = item {
            output.push_str(&indent_str);
            output.push_str("  - ");

            let mut sub_len_str = if let Some(marker) = options.length_marker {
                format!("{}{}", marker, sub_arr.len())
            } else {
                sub_arr.len().to_string()
            };
            if options.delimiter != ',' {
                sub_len_str.push(options.delimiter);
            }

            output.push_str(&format!("[{}]:", sub_len_str));

            let mut first = true;
            for sub_item in sub_arr {
                if !first {
                    output.push(options.delimiter);
                }
                first = false;

                if is_primitive(sub_item) {
                    encode_value(sub_item, options, 0, None, output);
                }
            }
            output.push('\n');
        }
    }
}

fn encode_list_array(arr: &[Value], options: &EncodeOptions, level: usize, key: Option<&str>, output: &mut String) {
    let indent_str = " ".repeat(level * options.indent);
    let mut len_str = if let Some(marker) = options.length_marker {
        format!("{}{}", marker, arr.len())
    } else {
        arr.len().to_string()
    };
    if options.delimiter != ',' {
        len_str.push(options.delimiter);
    }

    output.push_str(&indent_str);
    match key {
        Some(k) => output.push_str(&format!("{}[{}]:", k, len_str)),
        None => output.push_str(&format!("[{}]:", len_str)),
    }
    output.push('\n');

    for item in arr {
        output.push_str(&indent_str);
        output.push_str("  - ");

        match item {
            Value::Object(obj) => {
                // First field on the same line, rest indented
                let mut first = true;
                for (key, val) in obj {
                    if first {
                        output.push_str(key);
                        output.push_str(": ");
                        encode_value(val, options, level + 1, None, output);
                        first = false;
                    } else {
                        output.push('\n');
                        output.push_str(&indent_str);
                        output.push_str("    ");
                        output.push_str(key);
                        output.push_str(": ");
                        encode_value(val, options, level + 1, None, output);
                    }
                }
            }
            _ => {
                encode_value(item, options, level + 1, None, output);
            }
        }
        output.push('\n');
    }
}

fn encode_object(obj: &serde_json::Map<String, Value>, options: &EncodeOptions, level: usize, output: &mut String) {
    let indent_str = " ".repeat(level * options.indent);
    let mut first = true;

    for (key, value) in obj {
        if !first {
            output.push('\n');
        }
        first = false;

        match value {
            Value::Array(_) => {
                // For arrays, let encode_array handle the key name in the header
                encode_value(value, options, level, Some(key), output);
            }
            Value::Object(_) => {
                output.push_str(&indent_str);
                output.push_str(key);
                output.push_str(": ");
                output.push('\n');
                encode_value(value, options, level + 1, Some(key), output);
            }
            _ => {
                output.push_str(&indent_str);
                output.push_str(key);
                output.push_str(": ");
                encode_value(value, options, level + 1, Some(key), output);
            }
        }
    }
}

fn is_primitive(value: &Value) -> bool {
    matches!(value, Value::Null | Value::Bool(_) | Value::Number(_) | Value::String(_))
}

fn quote_string(s: &str, delimiter: char) -> String {
    // Check if quoting is needed
    let needs_quotes = s.is_empty()
        || s.starts_with(' ')
        || s.ends_with(' ')
        || s.contains(delimiter)
        || s.contains(':')
        || s.contains('[')
        || s.contains(']')
        || s.contains('{')
        || s.contains('}')
        || s.starts_with('-')
        || s == "true"
        || s == "false"
        || s == "null"
        || (s.chars().next().map(|c| c.is_ascii_digit()).unwrap_or(false) && s.parse::<f64>().is_ok());

    if !needs_quotes {
        return s.to_string();
    }

    // Escape in a single pass for performance
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for ch in s.chars() {
        match ch {
            '\\' => out.push_str("\\\\"),
            '"' => out.push_str("\\\""),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_encode_simple_object() {
        let obj = json!({
            "id": 123,
            "name": "Ada",
            "active": true
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("id: 123"));
        assert!(result.contains("name: Ada"));
        assert!(result.contains("active: true"));
    }

    #[test]
    fn test_encode_tabular_array() {
        let obj = json!({
            "items": [
                {"sku": "A1", "qty": 2, "price": 9.99},
                {"sku": "B2", "qty": 1, "price": 14.5}
            ]
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("items[2]{sku,qty,price}:"));
    }

    #[test]
    fn test_encode_inline_array() {
        let obj = json!({
            "tags": ["javascript", "typescript", "nodejs"]
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("tags[3]:"));
    }

    #[test]
    fn test_encode_inline_array_with_pipe_and_length_marker() {
        let obj = json!({
            "tags": ["a", "b", "c"]
        });
        let mut options = EncodeOptions::default();
        options.delimiter = '|';
        options.length_marker = Some('#');
        let result = encode(&obj, &options);
        assert!(result.contains("tags[#3|]:"));
        assert!(result.contains("a|b|c"));
    }

    #[test]
    fn test_encode_root_tabular_array_without_default_key() {
        let arr = json!([
            {"sku": "A1", "qty": 2, "price": 9.99},
            {"sku": "B2", "qty": 1, "price": 14.5}
        ]);
        let options = EncodeOptions::default();
        let result = encode(&arr, &options);
        // Expect root-level header without implicit key name
        assert!(result.starts_with("[2]{"));
        assert!(result.contains("sku,qty,price}:"));
    }

    #[test]
    fn test_quote_hyphen_leading_only() {
        let obj = json!({
            "a": "MOUSE-BT",
            "b": "-item"
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("a: MOUSE-BT"));
        assert!(result.contains("b: \"-item\""));
    }

    #[test]
    fn test_encode_empty_array_default() {
        let obj = json!({
            "empty": []
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert_eq!(result, "empty[0]:");
    }

    #[test]
    fn test_encode_empty_array_with_marker_and_pipe() {
        let mut options = EncodeOptions::default();
        options.length_marker = Some('#');
        options.delimiter = '|';
        let obj = json!({
            "empty": []
        });
        let result = encode(&obj, &options);
        assert_eq!(result, "empty[#0|]:");
    }

    #[test]
    fn test_encode_array_of_arrays() {
        let obj = json!({
            "matrix": [[1, 2], [3, 4]]
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("matrix[2]:"));
        assert!(result.contains("- [2]:1,2"));
        assert!(result.contains("- [2]:3,4"));
    }

    #[test]
    fn test_encode_list_array_mixed_objects() {
        let obj = json!({
            "items": [
                {"a": 1},
                {"a": 1, "b": 2}
            ]
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("items[2]:"));
        assert!(result.contains("- a: 1"));
        assert!(result.contains("b: 2"));
    }

    #[test]
    fn test_quote_various_strings() {
        let obj = json!({
            "s1": "",
            "s2": "  lead",
            "s3": "1.0",
            "s4": "true",
            "s5": "A:B"
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("s1: \"\""));
        assert!(result.contains("s2: \"  lead\""));
        assert!(result.contains("s3: \"1.0\""));
        assert!(result.contains("s4: \"true\""));
        assert!(result.contains("s5: \"A:B\""));
    }

    #[test]
    fn test_number_trimming() {
        let obj = json!({
            "f1": 2.500,
            "f2": 3.1400,
            "i1": 10
        });
        let options = EncodeOptions::default();
        let result = encode(&obj, &options);
        assert!(result.contains("f1: 2.5"));
        assert!(result.contains("f2: 3.14"));
        assert!(result.contains("i1: 10"));
    }
}
