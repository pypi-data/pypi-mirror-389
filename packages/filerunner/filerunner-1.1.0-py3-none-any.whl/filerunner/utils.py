from pathlib import Path


def get_file_paths(root_path: str | Path, pattern: str = "*") -> list[Path]:
    root = Path(root_path)
    return [p for p in root.rglob(pattern) if p.is_file()]
