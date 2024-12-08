import string
from typing import List, Any, Dict


def add_alphabet_keys(data: List[Any]) -> Dict[str, Any]:
    alphabet = string.ascii_uppercase
    result = {}

    for i, value in enumerate(data):
        if i < 26:
            key = alphabet[i]
        else:
            key = alphabet[(i // 26) - 1] + alphabet[i % 26]
        result[key] = value

    return result
