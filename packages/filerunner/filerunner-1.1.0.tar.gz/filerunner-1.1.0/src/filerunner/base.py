from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Literal

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)

Mode = Literal["multithreading", "multiprocessing"]


class FileRunner(ABC):
    def __init__(
        self,
        file_paths: Iterable[Path | str],
        max_workers: int = 4,
        mode: Mode = "multithreading",
        raise_on_error: bool = False,
    ):
        self.file_paths = file_paths
        if not self.file_paths:
            raise ValueError("file_paths cannot be empty.")

        self.max_workers = max_workers
        self.mode = mode
        self.raise_on_error = raise_on_error

    @abstractmethod
    def process_file(self, file_path: Path, *args, **kwargs): ...

    def run(self, *args, **kwargs):
        total_files = len(self.file_paths)

        executor_class = (
            ThreadPoolExecutor if self.mode == "thread" else ProcessPoolExecutor
        )

        with (
            executor_class(max_workers=self.max_workers) as executor,
            Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
            ) as progress,
        ):
            task = progress.add_task("Processing files...", total=total_files)
            futures = {
                executor.submit(self._safe_process, Path(f), *args, **kwargs): f
                for f in self.file_paths
            }

            for future in as_completed(futures):
                future.result()  # raises exception if any
                progress.update(task, advance=1)

    def _safe_process(self, file_path: Path, *args, **kwargs):
        try:
            self.process_file(file_path, *args, **kwargs)
        except Exception as e:
            self._on_error(file_path, e)

    def _on_error(self, file_path: Path, exception: Exception) -> None:
        if self.raise_on_error:
            raise exception
        else:
            print(f"Error processing {file_path}: {exception}")
