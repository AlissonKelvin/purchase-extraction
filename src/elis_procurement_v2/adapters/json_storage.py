import json
from pathlib import Path
from typing import Any


def save_json(
    data: dict[str, Any],
    file_path: str | Path,
) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ),
        encoding='utf-8',
    )
