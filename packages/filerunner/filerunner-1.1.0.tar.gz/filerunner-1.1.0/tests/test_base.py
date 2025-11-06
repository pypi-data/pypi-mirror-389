from pathlib import Path

from filerunner import FileRunner


class TestFileRunner:
    class MockFileRunner(FileRunner):
        def process_file(self, file_path):
            pass

    def test_initialization(self):
        runner = self.MockFileRunner(["/some/path"], max_workers=2)
        assert runner.file_paths == ["/some/path"]
        assert runner.max_workers == 2

    def test_safe_process_no_exception(self):
        runner = self.MockFileRunner("/some/path")
        runner._safe_process(Path("/some/file.txt"))

    def test_safe_process_with_exception(self):
        class ExceptionFileRunner(FileRunner):
            def process_file(self, file_path):
                raise ValueError("Test exception")

        runner = ExceptionFileRunner("/some/path")
        runner._on_error = lambda fp, e: setattr(self, "error_handled", True)
        self.error_handled = False
        runner._safe_process(Path("/some/file.txt"))
        assert self.error_handled
