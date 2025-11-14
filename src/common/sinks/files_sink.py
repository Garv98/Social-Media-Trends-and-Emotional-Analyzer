import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class FileSink:
    """Append events to JSONL files with simple time-based partitioning."""

    def __init__(self, root_dir: str = "data/raw", filename_pattern: str = "events-%Y-%m-%d.jsonl", partition_by: str = "date"):
        self.root = Path(root_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.pattern = filename_pattern
        assert partition_by in {"date", "hour"}
        self.partition_by = partition_by

    def _path_for_now(self) -> Path:
        now = datetime.utcnow()
        if self.partition_by == "hour":
            sub = now.strftime("%Y/%m/%d/%H")
        else:
            sub = now.strftime("%Y/%m/%d")
        dir_path = self.root / sub
        dir_path.mkdir(parents=True, exist_ok=True)
        fname = now.strftime(self.pattern)
        return dir_path / fname

    def write(self, event: Dict[str, Any]) -> None:
        path = self._path_for_now()
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def flush(self) -> None:
        # File appends are immediate; nothing to flush explicitly
        pass
