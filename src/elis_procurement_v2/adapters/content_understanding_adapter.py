from collections.abc import Mapping
from typing import Any


def extract_value(field: Any) -> Any:
    if not isinstance(field, Mapping):
        return None

    field_type = field.get('type')

    if field_type == 'string':
        return field.get('stringValue')

    if field_type in ('number', 'integer'):
        return field.get('numberValue')

    if field_type == 'array':
        return (
            [extract_value(item) for item in field.get('valueArray', [])]
            if field.get('valueArray') is not None
            else None
        )

    if field_type == 'object':
        value_object = field.get('valueObject')

        if value_object is None:
            return None

        return {key: extract_value(value) for key, value in value_object.items()}
    return None


def adapt_content_understanding(response: Mapping[str, Any]) -> dict[str, Any]:
    contents = response.get('result', {}).get('contents', [])

    if not contents:
        raise ValueError('No contents found in the response.')

    fields = contents[0].get('fields', {})

    return {key: extract_value(value) for key, value in fields.items()}
