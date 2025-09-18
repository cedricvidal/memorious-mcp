#!/usr/bin/env python3
"""Validate server.json against its $schema using jsonschema and requests.

Usage: python scripts/validate_server_json.py
"""
import json
import sys
from pathlib import Path

try:
    import requests
    import jsonschema
except Exception as e:
    print("Missing required packages: please install 'requests' and 'jsonschema'", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
SERVER_JSON = ROOT / "server.json"

if not SERVER_JSON.exists():
    print(f"server.json not found at {SERVER_JSON}", file=sys.stderr)
    sys.exit(2)

with SERVER_JSON.open() as f:
    data = json.load(f)

schema_url = data.get("$schema")
if not schema_url:
    print("No $schema entry found in server.json", file=sys.stderr)
    sys.exit(2)

print(f"Fetching schema from {schema_url} ...")
resp = requests.get(schema_url, timeout=10)
resp.raise_for_status()

schema = resp.json()

print("Validating server.json against schema...")
validator = jsonschema.Draft7Validator(schema)
errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
if not errors:
    print("Validation successful: server.json conforms to schema.")
    sys.exit(0)

print("Validation failed. Errors:")
for e in errors:
    path = ".".join(map(str, e.absolute_path)) or "<root>"
    print(f"- {path}: {e.message}")

sys.exit(1)
