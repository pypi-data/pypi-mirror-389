"""
Shared JSON parsing utilities for LLM responses.

Handles markdown code blocks and extracts structured data consistently.
"""

import json
import re
from typing import Any


def parse_llm_json_response(response: str) -> dict[str, Any]:
    """
    Parse JSON from LLM response, handling markdown code blocks.

    Args:
        response: Raw LLM response string

    Returns:
        Parsed dict, or {"score": -1.0, "reasoning": "error"} on failure
    """
    # Strip whitespace
    response = response.strip()

    # Remove markdown code blocks if present
    if "```" in response:
        parts = response.split("```")
        for part in parts:
            # Skip language identifiers (json, python, etc.)
            stripped = part.strip()
            if (
                stripped
                and not stripped.lower().startswith(
                    ("json", "python", "javascript", "js")
                )
                and "{" in stripped
                and "}" in stripped
            ):
                response = stripped
                break

    # Try to parse as JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from text
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass

    # Fallback: extract numeric score from text (preserves original behavior)
    # Look for patterns like "score: 8", "rating: 7.5", "8/10", or just numbers
    numbers = re.findall(r"\b-?\d+(?:\.\d+)?%?\b", response)
    if numbers:
        try:
            # Use the last number found (typically the score)
            score_str = numbers[-1].rstrip("%")
            score_val = float(score_str)
            return {
                "score": score_val,
                "reasoning": f"Fallback parsing: extracted score {score_val} from text",
            }
        except ValueError:
            pass

    # Final fallback - return error dict
    return {
        "score": -1.0,
        "reasoning": f"JSON parsing failed. Response preview: {response[:200]}",
    }
