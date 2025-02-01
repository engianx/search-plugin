import json

def load_json(json_string: str) -> dict:
    """Parse a JSON string.

    Args:
        json_string: The JSON string.

    Returns:
        The parsed JSON object as a Python dictionary.
    """
    try:

        return json.loads(json_string)

    except json.JSONDecodeError:
        # remove the leading and trailing backticks
        json_str = json_string.strip("```")

        if json_str.startswith("json"):
            json_str = json_str[4:]

        return json.loads(json_str)
