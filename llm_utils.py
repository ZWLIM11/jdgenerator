"""
llm_utils.py
Shared LLM helpers — with Qwen3 <think> tag stripping and num_ctx fix.
"""

import json
import re
import ollama

MODEL_NAME = "qwen3:8b"
OLLAMA_OPTIONS = {
    "temperature": 0.0,
    "top_p": 0.9,
    "seed": 42,
    "num_ctx": 8192,   # increase context window so long EAM outputs don't get cut
    "num_predict": 4096,  # max tokens to generate per call
}


def _strip_think_tags(text: str) -> str:
    """
    Qwen3 sometimes wraps its reasoning in <think>...</think> tags.
    Strip them so only the actual JSON output remains.
    """
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"```json|```", "", text)
    return text.strip()


def chat(prompt: str) -> str:
    """Send a single-turn prompt to the model and return cleaned text."""
    response = ollama.chat(
        model=MODEL_NAME,
        options=OLLAMA_OPTIONS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response["message"]["content"]
    return _strip_think_tags(raw)


def extract_json(text: str):
    """Strip markdown fences and parse the first JSON object or array found."""
    text = _strip_think_tags(text)

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try array
    arr_start = text.find("[")
    arr_end   = text.rfind("]") + 1
    if arr_start != -1 and arr_end > arr_start:
        try:
            return json.loads(text[arr_start:arr_end])
        except json.JSONDecodeError:
            pass

    # Try object
    obj_start = text.find("{")
    obj_end   = text.rfind("}") + 1
    if obj_start != -1 and obj_end > obj_start:
        try:
            return json.loads(text[obj_start:obj_end])
        except json.JSONDecodeError:
            pass

    raise ValueError("No JSON found in model response.")
