"""
json_validator.py
Harness Module 1 — validates JSON syntax of LLM output.
Includes truncation repair for common Qwen3 cutoff patterns.
"""

import json
import re


def _try_repair(text: str) -> str | None:
    """
    Attempt to repair truncated JSON by closing open structures.
    Handles the most common case: model cuts off mid-string or mid-array.
    """
    # Count open/close braces and brackets
    open_braces   = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")

    # Remove trailing partial token (unclosed string or value)
    repaired = text.rstrip()

    # Remove trailing comma before closing
    repaired = re.sub(r",\s*$", "", repaired)

    # Close open string if needed
    if repaired.count('"') % 2 != 0:
        repaired += '"'

    # Close structures
    repaired += "}" * open_braces + "]" * open_brackets

    return repaired if repaired != text else None


def validate_json(raw_text: str) -> dict:
    """
    Attempt to parse raw LLM output as JSON.
    Returns: {"valid": bool, "data": parsed | None, "errors": [str], "score": float}
    """
    errors = []

    # Strip think tags and markdown
    text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
    text = re.sub(r"```json|```", "", text).strip()

    # 1. Direct parse
    try:
        return {"valid": True, "data": json.loads(text), "errors": [], "score": 1.0}
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {e}")

    # 2. Extract array
    arr_match = re.search(r"\[.*\]", text, re.DOTALL)
    if arr_match:
        try:
            return {"valid": True, "data": json.loads(arr_match.group()),
                    "errors": ["Fixed: extracted array"], "score": 0.9}
        except json.JSONDecodeError:
            pass

    # 3. Extract object
    obj_match = re.search(r"\{.*\}", text, re.DOTALL)
    if obj_match:
        try:
            return {"valid": True, "data": json.loads(obj_match.group()),
                    "errors": ["Fixed: extracted object"], "score": 0.9}
        except json.JSONDecodeError:
            pass

    # 4. Try repair (truncation fix)
    for candidate in [text, arr_match.group() if arr_match else "", obj_match.group() if obj_match else ""]:
        if not candidate:
            continue
        repaired = _try_repair(candidate)
        if repaired:
            try:
                return {"valid": True, "data": json.loads(repaired),
                        "errors": ["Fixed: repaired truncated JSON"], "score": 0.7}
            except json.JSONDecodeError:
                pass

    errors.append("Array extraction failed")
    errors.append("Object extra")
    return {"valid": False, "data": None, "errors": errors, "score": 0.0}
