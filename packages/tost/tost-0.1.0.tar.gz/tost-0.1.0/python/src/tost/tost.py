"""
TOON Python API implementation

This module provides the Python interface for TOON encoding and decoding.
The actual implementation is provided by the Rust backend via PyO3 bindings.
"""

# Import from the Rust extension module
# Note: The Rust code creates a '_tost' module with encode/decode functions
# We need to import from the extension module created by maturin
try:
    # When built with maturin, the Rust extension is available as a native module
    # The module name is 'tost._tost' as specified in pyproject.toml
    from tost._tost import encode_py as _encode, decode_py as _decode
except ImportError:
    # Fallback for development or when Rust extension is not built
    def _encode(obj, indent=2, delimiter=",", length_marker=None):
        raise ImportError(
            "tost Rust extension not found. Please build the package using 'maturin develop' or 'maturin build'."
        )
    
    def _decode(tost_str):
        raise ImportError(
            "tost Rust extension not found. Please build the package using 'maturin develop' or 'maturin build'."
        )


def encode(obj, indent=2, delimiter=",", length_marker=None):
    """
    Encode a Python object to TOON format.
    
    Args:
        obj: Python object to encode (dict, list, primitive types)
        indent: Number of spaces per indentation level (default: 2)
        delimiter: Delimiter for array values and tabular rows (default: ',')
        length_marker: Optional marker to prefix array lengths (e.g., '#')
    
    Returns:
        str: TOON-formatted string
    
    Examples:
        >>> encode({"id": 123, "name": "Alice"})
        'id: 123\\nname: Alice'
        
        >>> encode({"items": [{"sku": "A1", "qty": 2}, {"sku": "B2", "qty": 1}]})
        'items[2]{sku,qty}:\\n  A1,2\\n  B2,1'
    """
    return _encode(obj, indent=indent, delimiter=delimiter, length_marker=length_marker)


def decode(tost_str):
    """
    Decode a TOON format string to a Python object.
    
    Args:
        tost_str: TOON-formatted string
    
    Returns:
        Python object (dict, list, or primitive type)
    
    Examples:
        >>> decode("id: 123\\nname: Alice")
        {'id': 123, 'name': 'Alice'}
        
        >>> decode("items[2]{sku,qty}:\\n  A1,2\\n  B2,1")
        {'items': [{'sku': 'A1', 'qty': 2}, {'sku': 'B2', 'qty': 1}]}
    """
    return _decode(tost_str)

