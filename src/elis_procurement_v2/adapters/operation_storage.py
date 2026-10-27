import json
from pathlib import Path


class OperationStorage:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def load(self) -> dict[str, dict[str, str]]:
        if not self.file_path.exists():
            return {}

        return json.loads(self.file_path.read_text(encoding='utf-8'))

    def save(self, operations: dict[str, dict[str, str]]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        temp_path = self.file_path.with_suffix('.tmp')
        temp_path.write_text(
            json.dumps(operations, indent=2, ensure_ascii=False),
            encoding='utf-8',
        )
        temp_path.replace(self.file_path)
