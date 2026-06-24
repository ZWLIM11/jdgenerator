"""
json_validator.py
Harness Module 1 — validates JSON syntax of LLM output.
"""

import json
import re


def validate_json(raw_text: str) -> dict:
    """
    Attempt to parse raw LLM output as JSON.
    Returns: {"valid": bool, "data": parsed | None, "errors": [str]}
    """
    errors = []
    text = re.sub(r"```json|```", "", raw_text).strip()

    # Try direct parse
    try:
        data = json.loads(text)
        return {"valid": True, "data": data, "errors": [], "score": 1.0}
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {str(e)}")

    # Try extracting array
    arr_match = re.search(r"\[.*\]", text, re.DOTALL)
    if arr_match:
        try:
            data = json.loads(arr_match.group())
            return {"valid": True, "data": data, "errors": ["Fixed: extracted array"], "score": 0.8}
        except json.JSONDecodeError:
            errors.append("Array extraction failed")

    # Try extracting object
    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        try:
            data = json.loads(obj_match.group())
            return {"valid": True, "data": data, "errors": ["Fixed: extracted object"], "score": 0.8}
        except json.JSONDecodeError:
            errors.append("Object extraction failed")

    return {"valid": False, "data": None, "errors": errors, "score": 0.0}
