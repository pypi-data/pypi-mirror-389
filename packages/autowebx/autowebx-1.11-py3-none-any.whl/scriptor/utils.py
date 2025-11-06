import re
from json import loads

from autowebx import int_input
from autowebx.auto_save_list import AutoSaveList

values = AutoSaveList('values.json')
states = AutoSaveList('states.json')


def classify_url_params(params: dict) -> dict[str, bool]:
    prompt = list()
    result = dict()
    for k, v in params.items():
        if (i := values.index(v)) >= 0:
            result[k] = states[i]

        else:
            prompt.append({
                'key': k,
                'value': v,
                'variable': ''
            })

    if len(prompt) > 0:
        print('Identify variable parameters (leave empty for constant).')
        for item in prompt:
            prompt_text = f"'{item['key']}': '{item['value']}'\nIs variable? "
            is_variable = bool(int_input(prompt_text, 0))
            result[item['key']] = is_variable
            values.append(item['value'])
            states.append(is_variable)
    return result


def to_snake_case(name: str) -> str:
    # Replace hyphens and spaces with underscores
    s = re.sub(r"[-\s]+", "_", name)
    # Add underscore before any capital letter preceded by a lowercase or digit
    s = re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", s)
    # Handle acronyms (e.g., "HTTPServer" → "http_server")
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    # Lowercase and clean multiple underscores
    return re.sub(r"_+", "_", s).strip("_").lower()


def is_json(string: str) -> bool:
    try:
        loads(string)
        return True
    except (ValueError, TypeError):
        return False


def generate_generic_pattern(text: str, value: str) -> tuple[str | None, str | None]:
    """
    Generate a regex pattern that matches the same structure as the given text,
    with only the variable part in a capture group.
    Works for both top-level and embedded query-string style keys.
    """
    esc_val = re.escape(value)

    # JSON-like "key":"value"
    m = re.search(r'"([A-Za-z0-9_\-]+)"\s*:\s*"' + esc_val + r'"', text)
    if m:
        key = m.group(1)
        val_group = r'(\d+)' if re.fullmatch(r'\d+', value) else r'((?:[^"\\]|\\.)+)'
        pat = rf'"{key}"\s*:\s*"{val_group}(?<!\\)"(?=\s*(?:[,}}\]]|$))'
        return key, pat

    # Query-style key=value at top level or inside quoted string
    m = re.search(r'([A-Za-z0-9_\-]+)=' + esc_val, text)
    if m:
        key = m.group(1)
        if re.fullmatch(r'\d+', value):
            val_group = r'(\d+)'
        elif re.fullmatch(r'[A-Za-z0-9+/=]+', value):
            val_group = r'([A-Za-z0-9+/=]+)'
        elif re.fullmatch(r'[A-Za-z0-9_-]+', value):
            val_group = r'([A-Za-z0-9_-]+)'
        else:
            val_group = r'([^"&,\s]+)'  # fallback for mixed text

        # pattern يسمح بالبحث داخل نصوص مقتبسة أيضاً
        pat = rf'{key}={val_group}(?=[^0-9A-Za-z_]|$)'
        return key, pat

    return None, None
