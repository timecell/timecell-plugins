#!/usr/bin/env python3
"""Validate a TimeCell profile.md for required fields and structure."""
import sys
import re


def validate_profile(path):
    """Validate profile file. Returns (valid: bool, errors: list[str])."""
    try:
        with open(path) as f:
            content = f.read()
    except FileNotFoundError:
        return False, [f"Profile not found: {path}"]

    errors = []
    warnings = []

    if not re.search(r"^-[^\S\n]*Name:[^\S\n]*\S", content, re.MULTILINE):
        errors.append("Missing required field: Name")
    if not re.search(r"^-[^\S\n]*Residency:[^\S\n]*\S", content, re.MULTILINE):
        errors.append("Missing required field: Residency")
    if not re.search(r"^-[^\S\n]*Base currency:[^\S\n]*\S", content, re.MULTILINE):
        errors.append("Missing required field: Base currency")
    if not re.search(r"^##\s*Goals", content, re.MULTILINE):
        errors.append("Missing required section: Goals")

    # Role field validation (optional — defaults to principal)
    role_match = re.search(r"^-[^\S\n]*[Rr]ole:[^\S\n]*(\S+)", content, re.MULTILINE)
    if role_match:
        role_value = role_match.group(1).strip().lower()
        valid_roles = {"principal", "operator"}
        if role_value not in valid_roles:
            warnings.append(
                f"Unknown role '{role_value}' — expected: {', '.join(sorted(valid_roles))}"
            )

    return len(errors) == 0, errors, warnings


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: validate-profile.py <path-to-profile.md>", file=sys.stderr)
        sys.exit(1)
    valid, errors, warnings = validate_profile(sys.argv[1])
    if not valid:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    print("Profile valid.")
    sys.exit(0)
