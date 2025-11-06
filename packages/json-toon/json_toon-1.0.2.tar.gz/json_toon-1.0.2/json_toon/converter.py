"""
json_toon.converter
-------------------
Convert JSON ↔ TOON (Token-Oriented Object Notation)
Lightweight encoder/decoder for LLM-friendly structured data.
"""

import json
from typing import Any, Dict, List, Tuple

# ==========================================================
# JSON → TOON
# ==========================================================

def json_to_toon(data: Any, indent: int = 0) -> str:
    """
    Convert Python object (JSON-like) into TOON text format.
    Handles nested dicts, lists, and primitive values.
    """
    pad = "  " * indent

    if isinstance(data, list):
        if not data:
            return pad + "[]"

        # Array of dicts -> table
        if all(isinstance(x, dict) for x in data):
            # Preserve key order from the first item; include any new keys later
            keys = list(data[0].keys())
            for item in data[1:]:
                for k in item.keys():
                    if k not in keys:
                        keys.append(k)

            header = pad + " | ".join(keys)
            rows = [
                pad + " | ".join(_cell_stringify(item.get(k, "")) for k in keys)
                for item in data
            ]
            return "\n".join([header] + rows)

        # List of primitives/mixed
        return pad + ", ".join(_cell_stringify(i) for i in data)

    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                nested = json_to_toon(value, indent + 1)
                lines.append(f"{pad}{key}:\n{nested}")
            else:
                lines.append(f"{pad}{key}: {_stringify(value)}")
        return "\n".join(lines)

    return pad + _stringify(data)


def _stringify(value: Any) -> str:
    """Convert any Python value to a clean TOON-safe string."""
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return str(value)
    return str(value)


def _cell_stringify(value: Any) -> str:
    """
    Stringify a value for table cells or simple lists.
    Use compact JSON for complex types so the decoder can restore them.
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"))
    return _stringify(value)


# ==========================================================
# TOON → JSON
# ==========================================================

def toon_to_json(toon_text: str) -> Any:
    """
    Parse TOON-formatted text back into JSON-compatible Python object.
    Handles indentation-based nesting, tables, and simple lists.
    """
    lines = [
        l.rstrip("\n")
        for l in toon_text.split("\n")
        if l.strip() and not l.strip().startswith("#")
    ]
    parsed, _ = _parse_block(lines, 0, 0)
    return parsed


def _parse_block(lines: List[str], start: int, base_indent: int) -> Tuple[Dict[str, Any], int]:
    """
    Parse a mapping block starting at `start` with indentation >= base_indent.
    Supports:
      - key: value
      - key: (nested dict/list/table)
      - key: <table header>  (inline header, rows below)
    """
    obj: Dict[str, Any] = {}
    i = start

    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip(" "))
        if indent < base_indent:
            break

        stripped = line.strip()

        # Expect "key:" or "key: value" here
        if ":" in stripped and not stripped.startswith("|"):
            key, *rest = stripped.split(":")
            key = key.strip()
            value_str = ":".join(rest).strip()

            if value_str == "":
                # Nested block begins on the next line — detect its type
                j = i + 1
                if j >= len(lines):
                    obj[key] = {}
                    i = j
                    continue

                next_line = lines[j]
                next_indent = len(next_line) - len(next_line.lstrip(" "))
                if next_indent < indent + 2:
                    obj[key] = {}
                    i = j
                    continue

                next_stripped = next_line.strip()

                # Case 1: Table with header on the first nested line
                if " | " in next_stripped and ":" not in next_stripped:
                    table, new_i = _parse_table_block_with_header(lines, j, indent + 2)
                    obj[key] = table
                    i = new_i
                    continue

                # Case 2: Nested mapping (starts with "child: value/...")
                if ":" in next_stripped:
                    sub_obj, new_i = _parse_block(lines, j, indent + 2)
                    obj[key] = sub_obj
                    i = new_i
                    continue

                # Case 3: Simple list (comma-separated, possibly across lines)
                arr, new_i = _parse_list_block(lines, j, indent + 2)
                obj[key] = arr
                i = new_i
                continue

            # Inline table header after colon (rare)
            if " | " in value_str and ":" not in value_str:
                header = [h.strip() for h in value_str.split("|")]
                rows: List[List[str]] = []
                j = i + 1
                while j < len(lines):
                    row_line = lines[j]
                    row_indent = len(row_line) - len(row_line.lstrip(" "))
                    if row_indent <= indent:
                        break
                    if "|" in row_line:
                        rows.append([c.strip() for c in row_line.strip().split("|")])
                        j += 1
                    else:
                        break

                out = []
                for r in rows:
                    d = {}
                    for idx, h in enumerate(header):
                        d[h] = parse_value(r[idx]) if idx < len(r) else ""
                    out.append(d)
                obj[key] = out
                i = j
                continue

            # Simple scalar
            obj[key] = parse_value(value_str)
            i += 1
            continue

        # Unexpected line type within a mapping — stop this block
        break

    return obj, i


def _parse_table_block_with_header(lines: List[str], i: int, base_indent: int) -> Tuple[List[Dict[str, Any]], int]:
    """
    Parse a table block whose first line at index i is the header (contains pipes).
    Returns (list_of_rows_as_dicts, new_index).
    """
    header_line = lines[i]
    header_indent = len(header_line) - len(header_line.lstrip(" "))
    header = [h.strip() for h in header_line.strip().split("|")]

    rows: List[List[str]] = []
    i += 1
    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip(" "))
        if indent < header_indent:
            break
        stripped = line.strip()
        if "|" not in stripped:
            break
        row = [c.strip() for c in stripped.split("|")]
        rows.append(row)
        i += 1

    out: List[Dict[str, Any]] = []
    for r in rows:
        d: Dict[str, Any] = {}
        for idx, key in enumerate(header):
            val = r[idx] if idx < len(r) else ""
            d[key] = parse_value(val)
        out.append(d)
    return out, i


def _parse_list_block(lines: List[str], start: int, base_indent: int) -> Tuple[List[Any], int]:
    """
    Parse a simple list written as one or more comma-separated lines
    at indentation >= base_indent.
    """
    items: List[Any] = []
    i = start
    while i < len(lines):
        line = lines[i]
        indent = len(line) - len(line.lstrip(" "))
        if indent < base_indent:
            break
        stripped = line.strip()

        # If a new mapping key appears at same or lower indent, stop
        if ":" in stripped:
            break

        parts = [p.strip() for p in stripped.split(",") if p.strip() != ""]
        for p in parts:
            items.append(parse_value(p))
        i += 1

    return items, i


# ==========================================================
# Utilities
# ==========================================================

def parse_value(v: str) -> Any:
    """Safely parse primitive values and JSON-encoded cells."""
    v = v.strip()

    # Try to parse JSON structures (used in table cells for nested values)
    if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")):
        try:
            return json.loads(v)
        except Exception:
            pass

    # Booleans
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False

    # Numbers (ints / floats, incl. negative)
    try:
        if "." in v and v.replace(".", "", 1).replace("-", "", 1).isdigit():
            return float(v)
        if v.replace("-", "", 1).isdigit():
            return int(v)
    except Exception:
        pass

    # Fallback: string
    return v


def to_json_str(toon_text: str) -> str:
    """Return pretty JSON string from TOON text."""
    return json.dumps(toon_to_json(toon_text), indent=2)
