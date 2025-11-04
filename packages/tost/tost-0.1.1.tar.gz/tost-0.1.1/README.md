# TOON Python API

TOON (Token-Oriented Object Notation) is a compact, human-readable data format designed to reduce token usage when passing data to large language models. Compared to JSON format, TOON can reduce token usage by 30-60%.

This project provides a Python API library with a Rust backend, delivering high-performance Python bindings through PyO3.

## Features

- ✅ **Encode and Decode**: Bidirectional conversion between Python objects and TOON format
- ✅ **Table Format Optimization**: Automatically detects uniform object arrays and compresses them using table format
- ✅ **Multiple Array Formats**: Supports inline arrays, table arrays, list arrays, and arrays of arrays
- ✅ **Nested Structures**: Full support for nested objects and arrays
- ✅ **Custom Options**: Supports custom indentation, delimiters, and length markers
- ✅ **High Performance**: Rust backend provides fast encoding/decoding performance

## Installation

```bash
pip install tost
```

**Requirements:**
- Python 3.8+

### Development Installation

If you need to install from source or for development:

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install maturin
pip install maturin

# Install from source
pip install .

# Or install in development mode (recommended for development)
maturin develop

# Or build wheel files
maturin build --release
```

## Usage Examples

### Basic Encoding

```python
from tost import encode

# Simple object
obj = {
    "id": 123,
    "name": "Ada Lovelace",
    "email": "ada@example.com",
    "active": True
}

result = encode(obj)
print(result)
# Output:
# id: 123
# name: Ada Lovelace
# email: ada@example.com
# active: true
```

### Table Format Arrays

```python
from tost import encode

# Table format array (auto-optimized)
products = {
    "items": [
        {"sku": "LAPTOP-15", "qty": 5, "price": 899.99},
        {"sku": "MOUSE-BT", "qty": 25, "price": 29.99},
        {"sku": "KEYBOARD-MX", "qty": 12, "price": 149.00}
    ]
}

result = encode(products)
print(result)
# Output:
# items[3]{sku,qty,price}:
#   LAPTOP-15,5,899.99
#   MOUSE-BT,25,29.99
#   KEYBOARD-MX,12,149
```

### Inline Arrays

```python
from tost import encode

# Inline array (primitive type array)
tags = {
    "tags": ["javascript", "typescript", "nodejs", "llm"]
}

result = encode(tags)
print(result)
# Output:
# tags[4]: javascript,typescript,nodejs,llm
```

### Nested Structures

```python
from tost import encode

order = {
    "orderId": "ORD-2025-001",
    "customer": {
        "name": "John Smith",
        "email": "john@example.com"
    },
    "items": [
        {"product": "Widget A", "quantity": 2, "price": 19.99},
        {"product": "Widget B", "quantity": 1, "price": 34.50}
    ],
    "total": 74.48,
    "tags": ["priority", "gift-wrap"]
}

result = encode(order)
print(result)
# Output:
# orderId: ORD-2025-001
# customer:
#   name: John Smith
#   email: john@example.com
# items[2]{product,quantity,price}:
#   Widget A,2,19.99
#   Widget B,1,34.5
# total: 74.48
# tags[2]: priority,gift-wrap
```

### Decoding

```python
from tost import decode

tost_str = """
id: 123
name: Ada Lovelace
active: true
items[2]{sku,qty}:
  A1,2
  B2,1
"""

result = decode(tost_str)
print(result)
# Output:
# {
#     'id': 123,
#     'name': 'Ada Lovelace',
#     'active': True,
#     'items': [
#         {'sku': 'A1', 'qty': 2},
#         {'sku': 'B2', 'qty': 1}
#     ]
# }
```

### Custom Options

```python
from tost import encode

obj = {
    "items": [
        {"sku": "A1", "qty": 2},
        {"sku": "B2", "qty": 1}
    ]
}

# Custom indentation, delimiter, and length marker
result = encode(
    obj,
    indent=4,           # 4-space indentation
    delimiter="|",       # Use pipe as delimiter
    length_marker="#"     # Use # as length marker
)
print(result)
# Output:
# items[#2|]{sku|qty}:
#     A1|2
#     B2|1
```

## API Reference

### `encode(obj, indent=2, delimiter=",", length_marker=None)`

Encode a Python object to TOON format string.

**Parameters:**
- `obj`: Python object to encode (dict, list, primitive types, etc.)
- `indent` (int, optional): Number of spaces per indentation level (default: 2)
- `delimiter` (str, optional): Delimiter for array values and table rows (default: ',')
- `length_marker` (str, optional): Prefix marker for array length (e.g., '#')

**Returns:**
- `str`: TOON format string

**Examples:**
```python
result = encode({"id": 123, "name": "Alice"})
result = encode(obj, indent=4, delimiter="|", length_marker="#")
```

### `decode(tost_str)`

Decode a TOON format string to Python object.

**Parameters:**
- `tost_str` (str): TOON format string

**Returns:**
- Python object (dict, list, or primitive type)

**Examples:**
```python
obj = decode("id: 123\nname: Alice")
```

## TOON Format Specification

### Object Format

```
key: value
```

### Table Array Format

When all objects in an array have the same keys and all values are primitive types, table format is used:

```
items[N]{field1,field2,field3}:
  value1,value2,value3
  value4,value5,value6
```

### Inline Array Format

Primitive type arrays use inline format:

```
tags[N]: value1,value2,value3
```

### List Format

Mixed or non-uniform arrays use list format:

```
items[N]:
  - value1
  - key: value
    other: value2
  - value3
```

### Array of Arrays Format

```
pairs[N]:
  - [M]: value1,value2
  - [M]: value3,value4
```

### Root-Level Arrays

When the root-level value is an array, use a header form without a key name:

```
[N]{field1,field2}:
  value1,value2
  value3,value4
```

Or for primitive type arrays:

```
[N]: value1,value2,value3
```

## Project Structure

```
tost/
├── Cargo.toml              # Rust workspace configuration
├── pyproject.toml          # Python package configuration
├── README.md                # Project documentation
├── rust/                    # Rust core library
│   ├── Cargo.toml
│   └── src/
│       ├── lib.rs          # Main library file (contains PyO3 bindings)
│       ├── encode.rs       # TOON encoding implementation
│       └── decode.rs        # TOON decoding implementation
└── python/                  # Python package
    ├── src/
    │   └── tost/           # Python package
    │       ├── __init__.py
    │       └── tost.py     # Python interface wrapper
    └── tests/              # Python tests
        └── test_tost.py
```

## Development

### Running Tests

```bash
# Rust tests
cd rust
cargo test

# Python tests
cd python
pytest tests/
```

### Building

```bash
# Development mode
maturin develop

# Release mode
maturin build --release
```

## License

MIT License

## References

- [TOON Format Specification](https://github.com/toon-format/toon)
- [PyO3 Documentation](https://pyo3.rs/)
- [maturin Documentation](https://maturin.rs/)

## Language

- [English](README.md) (current)
- [中文](README_CN.md)
