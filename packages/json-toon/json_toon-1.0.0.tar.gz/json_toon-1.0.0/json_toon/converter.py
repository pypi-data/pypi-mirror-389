"""
json_toon.converter
-------------------
Convert JSON ↔ TOON (Token-Oriented Object Notation)
Lightweight encoder/decoder for LLM-friendly structured data.
"""

import json
from typing import Any, Dict, List

def json_to_toon(data: Any, indent: int = 0) -> str:
    pad = "  " * indent

    if isinstance(data, list):
        if not data:
            return "[]"
        if isinstance(data[0], dict):
            # Convert list of dicts into table form
            keys = list(data[0].keys())
            header = pad + " | ".join(keys)
            rows = [
                pad + " | ".join(str(item.get(k, "")) for k in keys)
                for item in data
            ]
            return "\n".join([header] + rows)
        else:
            return pad + ", ".join(str(i) for i in data)

    elif isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                nested = json_to_toon(value, indent + 1)
                lines.append(f"{pad}{key}:\n{nested}")
            else:
                lines.append(f"{pad}{key}: {value}")
        return "\n".join(lines)

    else:
        return pad + str(data)


def toon_to_json(toon_text: str) -> Any:
    lines = [
        l.rstrip()
        for l in toon_text.split("\n")
        if l.strip() and not l.strip().startswith("#")
    ]

    result: Dict[str, Any] = {}
    current_key = None
    header = None
    rows: List[List[str]] = []

    for line in lines:
        if ":" in line:
            # Save any pending table before moving to next key
            if current_key and header and rows:
                result[current_key] = [dict(zip(header, r)) for r in rows]
                header, rows = None, []

            key, *rest = line.split(":")
            value = ":".join(rest).strip()

            if value == "":
                # Start of nested section (like an array)
                current_key = key.strip()
                continue

            if " | " in value:
                # Header for table
                current_key = key.strip()
                header = [h.strip() for h in value.split("|")]
                rows = []
                continue

            # Simple key:value
            result[key.strip()] = parse_value(value)

        elif " | " in line and header:
            # Table row
            row = [c.strip() for c in line.split("|")]
            rows.append(row)

    # Finalize last table
    if current_key and header and rows:
        result[current_key] = [dict(zip(header, r)) for r in rows]

    return result



def parse_value(v: str) -> Any:
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v.strip()


def to_json_str(toon_text: str) -> str:
    """Return JSON string from TOON."""
    return json.dumps(toon_to_json(toon_text), indent=2)
