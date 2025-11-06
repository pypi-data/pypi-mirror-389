# JSON Toon

Convert Python data structures to/from **TOON** (Token-Oriented Object Notation) - a lightweight, human-readable format optimized for LLM-friendly structured data.

## Installation

```bash
pip install json-toon
```

## What is TOON?

TOON is a Token-Oriented Object Notation format that represents structured data in a clean, readable way:
- Nested dictionaries with indentation
- Tables for lists of objects (using `|` separators)
- Comma-separated lists for simple arrays
- Human-readable and LLM-friendly

## Usage

### Convert Python Data to TOON Format

```python
from json_toon import json_to_toon

data = {
    "name": "Alice",
    "age": 30,
    "items": ["apple", "banana", "cherry"]
}

toon_string = json_to_toon(data)
print(toon_string)
# Output:
# name: Alice
# age: 30
# items:
#   apple, banana, cherry
```

### Convert TOON Back to Python Data

```python
from json_toon import toon_to_json

toon_text = """
name: Alice
age: 30
items:
  apple, banana, cherry
"""

data = toon_to_json(toon_text)
print(data)
# Output: {'name': 'Alice', 'age': 30, 'items': ['apple', 'banana', 'cherry']}
```

### Convert TOON to JSON String

```python
from json_toon import to_json_str

toon_text = """
name: Alice
age: 30
"""

json_string = to_json_str(toon_text)
print(json_string)
# Output: Pretty-printed JSON string
```

### Tables for Lists of Objects

```python
from json_toon import json_to_toon

users = [
    {"name": "Alice", "age": 30, "city": "NYC"},
    {"name": "Bob", "age": 25, "city": "LA"}
]

toon_string = json_to_toon(users)
print(toon_string)
# Output:
# name | age | city
# Alice | 30 | NYC
# Bob | 25 | LA
```

## API Reference

### `json_to_toon(data, indent=0)`
Convert Python object (dict, list, primitives) to TOON format string.

**Parameters:**
- `data`: Python object to convert
- `indent`: Starting indentation level (default: 0)

**Returns:** TOON-formatted string

### `toon_to_json(toon_text)`
Parse TOON-formatted text back into Python object.

**Parameters:**
- `toon_text`: TOON format string

**Returns:** Python object (dict, list, or primitive)

### `to_json_str(toon_text)`
Convert TOON text directly to JSON string.

**Parameters:**
- `toon_text`: TOON format string

**Returns:** Pretty-printed JSON string

## Development

To install in development mode:

```bash
pip install -e .
```

## License

MIT License - See LICENSE file for details.

