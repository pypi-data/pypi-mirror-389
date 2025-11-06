# JSON Toon

A Python library for JSON conversion utilities.

## Installation

```bash
pip install json-toon
```

## Usage

```python
from json_toon import converter

# Convert data to JSON
data = {"name": "example", "value": 42}
json_string = converter.convert_to_json(data)

# Convert JSON to data
parsed_data = converter.convert_from_json(json_string)
```

## Development

To install in development mode:

```bash
pip install -e .
```

## License

See LICENSE file for details.

