use serde_json::{Map, Value};
use regex::Regex;
use lazy_static::lazy_static;

lazy_static! {
    // key[len[delim]]{fields}:
    // key allows any non-structural token chars
    static ref TABULAR_HEADER_RE: Regex = Regex::new(
        r"^([^\[\]\{\}:]+)\[(#?\d+)([,\t\|])?\]\{([^}]+)\}:$"
    ).unwrap();
    // key[len[delim]]:
    static ref ARRAY_HEADER_WITH_KEY_RE: Regex = Regex::new(
        r"^([^\[\]\{\}:]+)\[(#?\d+)([,\t\|])?\]:$"
    ).unwrap();
    // [len[delim]]:
    static ref ARRAY_HEADER_RE: Regex = Regex::new(
        r"^\[(#?\d+)([,\t\|])?\]:$"
    ).unwrap();
}

pub fn decode(input: &str) -> Result<Value, String> {
    let lines: Vec<&str> = input.lines().collect();
    if lines.is_empty() {
        return Ok(Value::Null);
    }

    // Check if root is an array
    if let Some(first_line) = lines.first() {
        if first_line.trim().starts_with('[') {
            let (_consumed, value) = decode_array_root(&lines, 0)?;
            return Ok(value);
        }
    }

    // Otherwise, decode as object
    let mut result = Map::new();
    let mut i = 0;
    while i < lines.len() {
        let (consumed, key, value) = decode_object_entry(&lines, i)?;
        result.insert(key, value);
        i += consumed;
    }

    Ok(Value::Object(result))
}

fn decode_array_root(lines: &[&str], start: usize) -> Result<(usize, Value), String> {
    if start >= lines.len() {
        return Err("Unexpected end of input".to_string());
    }

    let first_line = lines[start].trim();
    
    // Parse [N]: format (support inline by parsing header slice)
    let header_slice = if let Some(cp) = first_line.find(':') {
        &first_line[..=cp]
    } else {
        first_line
    };
    if let Some((len, delim_opt)) = parse_array_header(header_slice) {
        let len = len;
        
        // Check if it's inline format (same line)
        if first_line.contains(':') {
            let colon_pos = first_line.find(':').unwrap();
            let after_colon = &first_line[colon_pos + 1..].trim();
            if !after_colon.is_empty() {
                // Inline format: [N]: value1,value2,...
                return decode_inline_array(after_colon, len, delim_opt).map(|v| (1, v));
            }
        }

        // List format: [N]: followed by lines with -
        let mut items = Vec::new();
        let mut i = start + 1;
        let mut count = 0;
        
        while i < lines.len() && count < len {
            let line = lines[i].trim();
            if line.starts_with("- ") {
                let (item, consumed) = decode_list_item(lines, i)?;
                items.push(item);
                i += consumed;
                count += 1;
            } else if line.is_empty() {
                i += 1;
            } else {
                break;
            }
        }

        Ok((i - start, Value::Array(items)))
    } else {
        Err(format!("Invalid array header: {}", first_line))
    }
}

fn decode_object_entry(lines: &[&str], start: usize) -> Result<(usize, String, Value), String> {
    if start >= lines.len() {
        return Err("Unexpected end of input".to_string());
    }

    let line = lines[start];
    let trimmed = line.trim();
    
    // Check for tabular format: key[N]{field1,field2}:
    // First check if this line has a tabular header (might be indented)
    if let Some((key, len, delim_opt, fields)) = parse_tabular_header(trimmed) {
        let mut items = Vec::new();
        let mut i = start + 1;
        let mut count = 0;
        
        while i < lines.len() && count < len {
            let row_line = lines[i].trim();
            if row_line.is_empty() {
                i += 1;
                continue;
            }
            
            let obj = decode_tabular_row(row_line, &fields, delim_opt)?;
            items.push(Value::Object(obj));
            i += 1;
            count += 1;
        }

        return Ok((i - start, key, Value::Array(items)));
    }
    
    // Check if next line is a tabular header (for nested objects)
    // This handles cases like:
    //   items:
    //     items[2]{sku,qty}:
    //       A1,2
    //       B2,1
    if start + 1 < lines.len() {
        let current_line = lines[start].trim();
        let next_line = lines[start + 1].trim();
        
        // Check if current line is a simple key: value line
        if let Some(colon_pos) = current_line.find(':') {
            let current_key = current_line[..colon_pos].trim();
            let after_colon = current_line[colon_pos + 1..].trim();
            
            // If current line is just "key:" (no value), and next line is a tabular header
            if after_colon.is_empty() {
                if let Some((_key, len, delim_opt, fields)) = parse_tabular_header(next_line) {
                    // This is a nested tabular array
                    let mut items = Vec::new();
                    let mut i = start + 2;
                    let mut count = 0;
                    
                    while i < lines.len() && count < len {
                        let row_line = lines[i].trim();
                        if row_line.is_empty() {
                            i += 1;
                            continue;
                        }
                        
                        let obj = decode_tabular_row(row_line, &fields, delim_opt)?;
                        items.push(Value::Object(obj));
                        i += 1;
                        count += 1;
                    }
                    
                    return Ok((i - start, current_key.to_string(), Value::Array(items)));
                }
            }
        }
    }

    // Check for array format: key[N]: (support inline by parsing header slice)
    let header_slice = if let Some(cp) = trimmed.find(':') { &trimmed[..=cp] } else { trimmed };
    if let Some((key, len, delim_opt)) = parse_array_header_with_key(header_slice) {
        // Check if inline format
        if trimmed.contains(':') {
            let colon_pos = trimmed.find(':').unwrap();
            let after_colon = &trimmed[colon_pos + 1..].trim();
            if !after_colon.is_empty() {
                // Inline array
                let value = decode_inline_array(after_colon, len, delim_opt)?;
                return Ok((1, key, value));
            }
        }

        // List format or array of arrays
        let mut i = start + 1;
        let mut items = Vec::new();
        let mut count = 0;

        // Check if it's array of arrays (first item starts with - [N]:)
        if i < lines.len() {
            let next_line = lines[i].trim();
            if next_line.starts_with("- [") {
                // Array of arrays
                while i < lines.len() && count < len {
                    let line = lines[i].trim();
                    if line.starts_with("- [") {
                        let array_value = decode_array_of_arrays_item(line)?;
                        items.push(array_value);
                        i += 1;
                        count += 1;
                    } else if line.is_empty() {
                        i += 1;
                    } else {
                        break;
                    }
                }
                return Ok((i - start, key, Value::Array(items)));
            }
        }

        // Regular list format
        while i < lines.len() && count < len {
            let line = lines[i].trim();
            if line.starts_with("- ") {
                let (item, consumed) = decode_list_item(lines, i)?;
                items.push(item);
                i += consumed;
                count += 1;
            } else if line.is_empty() {
                i += 1;
            } else {
                break;
            }
        }

        return Ok((i - start, key, Value::Array(items)));
    }

    // Regular key: value format
    if let Some(colon_pos) = trimmed.find(':') {
        let key = trimmed[..colon_pos].trim().to_string();
        let value_str = trimmed[colon_pos + 1..].trim();

        // Check if value is on same line
        if !value_str.is_empty() && !value_str.starts_with('\n') {
            let value = decode_value(value_str)?;
            return Ok((1, key, value));
        }

        // Value is on next line(s) - check indentation to decide nested vs empty
        let next_line_idx = start + 1;
        if next_line_idx < lines.len() {
            let current_indent = get_indent_level(lines[start]);
            let next_indent = get_indent_level(lines[next_line_idx]);
            if next_indent > current_indent {
                // Nested object/array under this key
                let (consumed, value) = decode_nested_value(lines, next_line_idx, current_indent)?;
                return Ok((consumed + 1, key, value));
            } else {
                // Next line is not nested; this key has an empty value
                return Ok((1, key, Value::Null));
            }
        }

        // No next line: treat as empty
        return Ok((1, key, Value::Null));
    }

    Err(format!("Invalid line format: {}", line))
}

fn parse_tabular_header(line: &str) -> Option<(String, usize, Option<char>, Vec<String>)> {
    // Format: key[N][delim]{field1<delim>field2,...} with optional #
    let caps = TABULAR_HEADER_RE.captures(line)?;
    let key = caps.get(1)?.as_str().to_string();
    let len_str = caps.get(2)?.as_str();
    let len: usize = len_str.strip_prefix('#').unwrap_or(len_str).parse().ok()?;
    let delim_opt = caps.get(3).and_then(|m| m.as_str().chars().next());
    let fields_str = caps.get(4)?.as_str();

    // Determine delimiter to split fields
    let split_delim = if let Some(d) = delim_opt {
        d
    } else if fields_str.contains('\t') {
        '\t'
    } else if fields_str.contains('|') {
        '|'
    } else {
        ','
    };
    let fields: Vec<String> = fields_str
        .split(split_delim)
        .map(|s| s.trim().to_string())
        .collect();

    Some((key, len, delim_opt, fields))
}

fn parse_array_header_with_key(line: &str) -> Option<(String, usize, Option<char>)> {
    // Format: key[N][delim]: or key[#N][delim]:
    let caps = ARRAY_HEADER_WITH_KEY_RE.captures(line)?;
    let key = caps.get(1)?.as_str().to_string();
    let len_str = caps.get(2)?.as_str();
    let len: usize = len_str.strip_prefix('#').unwrap_or(len_str).parse().ok()?;
    let delim_opt = caps.get(3).and_then(|m| m.as_str().chars().next());
    Some((key, len, delim_opt))
}

fn parse_array_header(line: &str) -> Option<(usize, Option<char>)> {
    // Format: [N][delim]: or [#N][delim]:
    let caps = ARRAY_HEADER_RE.captures(line)?;
    let len_str = caps.get(1)?.as_str();
    let len = len_str.strip_prefix('#').unwrap_or(len_str).parse().ok()?;
    let delim_opt = caps.get(2).and_then(|m| m.as_str().chars().next());
    Some((len, delim_opt))
}

fn decode_tabular_row(line: &str, fields: &[String], delim_opt: Option<char>) -> Result<Map<String, Value>, String> {
    // Prefer header's delimiter, fallback to scanning
    let delimiter = if let Some(d) = delim_opt {
        d
    } else if line.contains('\t') {
        '\t'
    } else if line.contains('|') {
        '|'
    } else {
        ','
    };

    let values: Vec<&str> = line.split(delimiter).map(|s| s.trim()).collect();
    if values.len() != fields.len() {
        return Err(format!("Row has {} values but expected {}", values.len(), fields.len()));
    }

    let mut obj = Map::new();
    for (field, value_str) in fields.iter().zip(values.iter()) {
        let value = decode_value(value_str)?;
        obj.insert(field.clone(), value);
    }

    Ok(obj)
}

fn decode_inline_array(line: &str, len: usize, delim_opt: Option<char>) -> Result<Value, String> {
    // Prefer header's delimiter, fallback to scanning
    let delimiter = if let Some(d) = delim_opt {
        d
    } else if line.contains('\t') {
        '\t'
    } else if line.contains('|') {
        '|'
    } else {
        ','
    };

    let values: Vec<&str> = line.split(delimiter).map(|s| s.trim()).collect();
    if values.len() != len {
        return Err(format!("Array has {} values but expected {}", values.len(), len));
    }

    let mut items = Vec::new();
    for value_str in values {
        items.push(decode_value(value_str)?);
    }

    Ok(Value::Array(items))
}

fn decode_array_of_arrays_item(line: &str) -> Result<Value, String> {
    // Format: - [N]: value1,value2,...
    let trimmed = line.strip_prefix("- ").unwrap_or(line).trim();
    
    if let Some(colon_pos) = trimmed.find(':') {
        let header = &trimmed[..colon_pos];
        let values_str = &trimmed[colon_pos + 1..].trim();
        
        if let Some((len, delim_opt)) = parse_array_header(&format!("{}:", header)) {
            return decode_inline_array(values_str, len, delim_opt);
        }
    }
    
    Err(format!("Invalid array of arrays format: {}", line))
}

fn decode_list_item(lines: &[&str], start: usize) -> Result<(Value, usize), String> {
    if start >= lines.len() {
        return Err("Unexpected end of input".to_string());
    }

    let line = lines[start];
    let trimmed = line.strip_prefix("- ").unwrap_or(line).trim();

    // Check if it's a primitive
    if !trimmed.contains(':') {
        return Ok((decode_value(trimmed)?, 1));
    }

    // It's an object
    let colon_pos = trimmed.find(':').unwrap();
    let key = trimmed[..colon_pos].trim().to_string();
    let value_str = trimmed[colon_pos + 1..].trim();

    let mut obj = Map::new();
    
    if !value_str.is_empty() {
        let value = decode_value(value_str)?;
        obj.insert(key, value);
    } else {
        obj.insert(key, Value::Null);
    }

    // Check for more fields on next lines
    let indent = get_indent_level(lines[start]);
    let mut i = start + 1;
    
    while i < lines.len() {
        let next_line = lines[i];
        let next_indent = get_indent_level(next_line);
        
        if next_indent <= indent {
            break;
        }

        let trimmed_line = next_line.trim();
        if let Some(colon_pos) = trimmed_line.find(':') {
            let key = trimmed_line[..colon_pos].trim().to_string();
            let value_str = trimmed_line[colon_pos + 1..].trim();
            
            let value = if !value_str.is_empty() {
                decode_value(value_str)?
            } else {
                Value::Null
            };
            
            obj.insert(key, value);
        }
        
        i += 1;
    }

    Ok((Value::Object(obj), i - start))
}

fn decode_nested_value(lines: &[&str], start: usize, _parent_indent: usize) -> Result<(usize, Value), String> {
    if start >= lines.len() {
        return Err("Unexpected end of input".to_string());
    }

    let first_line = lines[start].trim();
    
    // Check if it's an array
    if first_line.starts_with('[') || first_line.contains('[') {
        return decode_array_root(lines, start);
    }

    // It's a nested object
    let mut obj = Map::new();
    let mut i = start;
    let indent = get_indent_level(lines[start]);

    while i < lines.len() {
        let line = lines[i];
        let line_indent = get_indent_level(line);
        
        if line_indent < indent {
            break;
        }

        let trimmed = line.trim();
        if trimmed.is_empty() {
            i += 1;
            continue;
        }

        if let Some(colon_pos) = trimmed.find(':') {
            let key = trimmed[..colon_pos].trim().to_string();
            let value_str = trimmed[colon_pos + 1..].trim();

            if !value_str.is_empty() {
                let value = decode_value(value_str)?;
                obj.insert(key, value);
                i += 1;
            } else {
                // Check if nested
                if i + 1 < lines.len() {
                    let next_indent = get_indent_level(lines[i + 1]);
                    if next_indent > line_indent {
                        let (consumed, value) = decode_nested_value(lines, i + 1, line_indent)?;
                        obj.insert(key, value);
                        i += consumed + 1;
                    } else {
                        obj.insert(key, Value::Null);
                        i += 1;
                    }
                } else {
                    obj.insert(key, Value::Null);
                    i += 1;
                }
            }
        } else {
            i += 1;
        }
    }

    Ok((i - start, Value::Object(obj)))
}

fn decode_value(s: &str) -> Result<Value, String> {
    let trimmed = s.trim();
    
    // Null
    if trimmed == "null" {
        return Ok(Value::Null);
    }
    
    // Boolean
    if trimmed == "true" {
        return Ok(Value::Bool(true));
    }
    if trimmed == "false" {
        return Ok(Value::Bool(false));
    }
    
    // String (quoted)
    if trimmed.starts_with('"') && trimmed.ends_with('"') {
        let unquoted = &trimmed[1..trimmed.len() - 1];
        let unescaped = unquoted
            .replace("\\\"", "\"")
            .replace("\\\\", "\\")
            .replace("\\n", "\n")
            .replace("\\r", "\r")
            .replace("\\t", "\t");
        return Ok(Value::String(unescaped));
    }
    
    // Number
    if let Ok(i) = trimmed.parse::<i64>() {
        return Ok(Value::Number(i.into()));
    }
    if let Ok(f) = trimmed.parse::<f64>() {
        return Ok(Value::Number(serde_json::Number::from_f64(f).unwrap_or(0.into())));
    }
    
    // Unquoted string
    Ok(Value::String(trimmed.to_string()))
}

fn get_indent_level(line: &str) -> usize {
    line.chars().take_while(|c| c.is_whitespace()).count()
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decode_inline_array_with_pipe_and_length_marker() {
        let s = "tags[#3|]: a|b|c";
        let v = decode(s).unwrap();
        match v {
            Value::Object(map) => {
                let arr = map.get("tags").unwrap().as_array().unwrap();
                assert_eq!(arr.len(), 3);
                assert_eq!(arr[0], Value::String("a".into()));
            }
            _ => panic!("expected object"),
        }
    }

    #[test]
    fn test_decode_tabular_with_tab_delimiter() {
        let s = "users[2\t]{id\tname}:\n  1\tAlice\n  2\tBob";
        let v = decode(s).unwrap();
        match v {
            Value::Object(map) => {
                let arr = map.get("users").unwrap().as_array().unwrap();
                assert_eq!(arr.len(), 2);
                assert_eq!(arr[0]["id"], Value::Number(1.into()));
                assert_eq!(arr[0]["name"], Value::String("Alice".into()));
            }
            _ => panic!("expected object"),
        }
    }

    #[test]
    fn test_decode_array_root_inline_with_pipe() {
        let s = "[#3|]: a|b|c";
        let (consumed, v) = decode_array_root(&s.lines().collect::<Vec<_>>(), 0).unwrap();
        assert_eq!(consumed, 1);
        match v {
            Value::Array(arr) => {
                assert_eq!(arr.len(), 3);
            }
            _ => panic!("expected array"),
        }
    }

    #[test]
    fn test_decode_mismatched_tabular_row_count_error() {
        let s = "items[2]{a,b}:\n  1,2\n  3";
        let out = decode(s);
        assert!(out.is_err());
    }

    #[test]
    fn test_decode_empty_array_header() {
        let s = "items[0]:";
        let v = decode(s).unwrap();
        match v {
            Value::Object(map) => {
                let arr = map.get("items").unwrap().as_array().unwrap();
                assert_eq!(arr.len(), 0);
            }
            _ => panic!("expected object with empty array"),
        }
    }

    #[test]
    fn test_decode_array_of_arrays_with_marker_and_pipe() {
        let s = "matrix[#2|]:\n  - [#2|]: 1|2\n  - [#2|]: 3|4";
        let v = decode(s).unwrap();
        match v {
            Value::Object(map) => {
                let arr = map.get("matrix").unwrap().as_array().unwrap();
                assert_eq!(arr.len(), 2);
                assert_eq!(arr[0], Value::Array(vec![Value::Number(1.into()), Value::Number(2.into())]));
                assert_eq!(arr[1], Value::Array(vec![Value::Number(3.into()), Value::Number(4.into())]));
            }
            _ => panic!("expected object"),
        }
    }

    #[test]
    fn test_decode_nested_object_basic() {
        let s = "user:\n  id: 1\n  name: Alice";
        let v = decode(s).unwrap();
        match v {
            Value::Object(map) => {
                let user = map.get("user").unwrap().as_object().unwrap();
                assert_eq!(user.get("id").unwrap(), &Value::Number(1.into()));
                assert_eq!(user.get("name").unwrap(), &Value::String("Alice".into()));
            }
            _ => panic!("expected object"),
        }
    }
}
