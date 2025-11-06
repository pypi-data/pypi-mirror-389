from filerunner.utils import get_file_paths


class TestUtils:
    def test_get_file_paths(self, tmp_path):
        # Create some test files
        (tmp_path / "file1.txt").write_text("Hello")
        (tmp_path / "file2.log").write_text("World")
        (tmp_path / "script.py").write_text("print('Hi')")

        # Test pattern matching
        txt_files = get_file_paths(tmp_path, pattern="*.txt")
        assert len(txt_files) == 1
        assert txt_files[0].name == "file1.txt"

        py_files = get_file_paths(tmp_path, pattern="*.py")
        assert len(py_files) == 1
        assert py_files[0].name == "script.py"

        all_files = get_file_paths(tmp_path)
        assert len(all_files) == 3
