# Dedal library - Wrapper over Spack for building multiple target
# environments: ESD, Virtual Boxes, HPC compatible kernels, etc.

#  (c) Copyright 2025 Dedal developers

#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import logging
import os
import subprocess

import pytest
from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock
from dedal.utils.utils import clean_up, file_exists_and_not_empty, log_command, run_command, get_first_word, \
    count_files_in_folder, resolve_path, delete_file


@pytest.fixture
def temp_directories(tmp_path):
    """
    Create temporary directories with files and subdirectories for testing.
    """
    test_dirs = []

    for i in range(3):
        dir_path = tmp_path / f"test_dir_{i}"
        dir_path.mkdir()
        test_dirs.append(str(dir_path))

        # Add a file to the directory
        file_path = dir_path / f"file_{i}.txt"
        file_path.write_text(f"This is a test file in {dir_path}")

        # Add a subdirectory with a file
        sub_dir = dir_path / f"subdir_{i}"
        sub_dir.mkdir()
        sub_file = sub_dir / f"sub_file_{i}.txt"
        sub_file.write_text(f"This is a sub file in {sub_dir}")

    return test_dirs


def test_clean_up(temp_directories, mocker):
    """
    Test the clean_up function to ensure directories and contents are removed.
    """
    # Mock the logger using pytest-mock's mocker fixture
    mock_logger = mocker.MagicMock()

    # Ensure directories exist before calling clean_up
    for dir_path in temp_directories:
        assert Path(dir_path).exists()

    clean_up(temp_directories, mock_logger)

    for dir_path in temp_directories:
        assert not Path(dir_path).exists()

    for dir_path in temp_directories:
        mock_logger.info.assert_any_call(f"Removing {Path(dir_path).resolve()}")


def test_clean_up_nonexistent_dirs(mocker):
    """
    Test the clean_up function with nonexistent directories.
    """
    # Mock the logger using pytest-mock's mocker fixture
    mock_logger = mocker.MagicMock()
    nonexistent_dirs = ["nonexistent_dir_1", "nonexistent_dir_2"]

    clean_up(nonexistent_dirs, mock_logger)

    for dir_path in nonexistent_dirs:
        mock_logger.info.assert_any_call(f"{Path(dir_path).resolve()} does not exist")


def test_file_does_not_exist(tmp_path: Path):
    non_existent_file = tmp_path / "non_existent.txt"
    assert not file_exists_and_not_empty(non_existent_file)


def test_file_exists_but_empty(tmp_path: Path):
    empty_file = tmp_path / "empty.txt"
    # Create an empty file
    empty_file.touch()
    assert not file_exists_and_not_empty(empty_file)


def test_file_exists_and_not_empty(tmp_path: Path):
    non_empty_file = tmp_path / "non_empty.txt"
    non_empty_file.write_text("Some content")
    assert file_exists_and_not_empty(non_empty_file)


def test_log_command():
    results = MagicMock()
    results.stdout = "Test output"
    results.stderr = "Test error"
    mock_file = mock_open()

    with patch("builtins.open", mock_file):
        log_command(results, "logfile.log")

    mock_file.assert_called_once_with("logfile.log", "w")
    handle = mock_file()
    handle.write.assert_any_call("Test output")
    handle.write.assert_any_call("\n--- STDERR ---\n")
    handle.write.assert_any_call("Test error")


def test_run_command_success(mocker):
    mock_subprocess = mocker.patch("subprocess.run", return_value=MagicMock(returncode=0))
    mock_logger = MagicMock()
    result = run_command('bash', '-c', 'echo hello', logger=mock_logger, info_msg="Running echo")
    mock_logger.info.assert_called_with("Running echo: args: ('bash', '-c', 'echo hello')")
    mock_subprocess.assert_called_once_with(('bash', '-c', 'echo hello'))
    assert result.returncode == 0


def test_run_command_not_found(mocker):
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)
    mock_logger = MagicMock()
    run_command("invalid_command", logger=mock_logger)
    mock_logger.error.assert_called_with("Command not found. Please check the command syntax.")


def test_run_command_permission_error(mocker):
    mocker.patch("subprocess.run", side_effect=PermissionError)
    mock_logger = MagicMock()
    run_command("restricted_command", logger=mock_logger)
    mock_logger.error.assert_called_with("Permission denied. Try running with appropriate permissions.")


def test_run_command_timeout(mocker):
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=5))
    mock_logger = MagicMock()
    run_command("test", logger=mock_logger)
    mock_logger.error.assert_called_with("Command timed out. Try increasing the timeout duration.")


def test_run_command_os_error(mocker):
    mocker.patch("subprocess.run", side_effect=OSError("OS Error"))
    mock_logger = MagicMock()
    run_command("test", logger=mock_logger)
    mock_logger.error.assert_called_with("OS error occurred: OS Error")


def test_run_command_unexpected_exception(mocker):
    mocker.patch("subprocess.run", side_effect=Exception("Unexpected Error"))
    mock_logger = MagicMock()
    run_command("test", logger=mock_logger)
    mock_logger.error.assert_called_with("An unexpected error occurred: Unexpected Error")


def test_run_command_called_process_error(mocker):
    mocker.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "test"))
    mock_logger = MagicMock()
    run_command("test", logger=mock_logger, exception_msg="Process failed")
    mock_logger.error.assert_called_with("Process failed: Command 'test' returned non-zero exit status 1.")


def test_get_first_word_basic():
    assert get_first_word("Hello world") == "Hello"


def test_get_first_word_single_word():
    assert get_first_word("word") == "word"


def test_get_first_word_leading_whitespace():
    assert get_first_word("   leading spaces") == "leading"


def test_get_first_word_empty_string():
    assert get_first_word("") == ""


def test_get_first_word_whitespace_only():
    assert get_first_word("   \t  ") == ""


def test_get_first_word_with_punctuation():
    assert get_first_word("Hello, world!") == "Hello,"


def test_get_first_word_newline_delimiter():
    assert get_first_word("First line\nSecond line") == "First"


def test_count_files_in_folder_counts_files_only(tmp_path):
    # create files and subdirectories
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file3 = tmp_path / "c.txt"
    subdir = tmp_path / "subfolder"
    subdir_file = subdir / "d.txt"
    file1.write_text("data1")
    file2.write_text("data2")
    file3.write_text("data3")
    subdir.mkdir()
    subdir_file.write_text("data4")
    count = count_files_in_folder(tmp_path)
    assert count == 4


def test_count_files_in_folder_empty(tmp_path):
    count = count_files_in_folder(tmp_path)
    assert count == 0


def test_count_files_in_folder_only_dirs(tmp_path):
    (tmp_path / "dir1").mkdir()
    (tmp_path / "dir2").mkdir()
    count = count_files_in_folder(tmp_path)
    assert count == 0


def test_count_files_in_folder_path_is_file(tmp_path):
    file_path = tmp_path / "single.txt"
    file_path.write_text("content")
    assert count_files_in_folder(file_path) == 0


def test_delete_file_success(tmp_path, caplog):
    target = tmp_path / "temp.txt"
    target.write_text("to be deleted")
    logger = logging.getLogger("delete_success_test")
    caplog.set_level(logging.DEBUG, logger=logger.name)
    result = delete_file(str(target), logger)
    assert result is True
    assert not target.exists()
    assert any(rec.levelno == logging.DEBUG for rec in caplog.records)
    assert "deleted" in " ".join(rec.getMessage() for rec in caplog.records).lower()


def test_delete_file_not_found(tmp_path, caplog):
    missing = tmp_path / "no_such_file.txt"
    logger = logging.getLogger("delete_notfound_test")
    caplog.set_level(logging.ERROR, logger=logger.name)
    result = delete_file(str(missing), logger)
    assert result is False
    assert any(rec.levelno >= logging.WARNING for rec in caplog.records)
    combined_logs = " ".join(rec.getMessage() for rec in caplog.records).lower()
    assert "not found" in combined_logs or "no such file" in combined_logs


def test_delete_file_directory_input(tmp_path, caplog):
    dir_path = tmp_path / "dir_to_delete"
    dir_path.mkdir()
    logger = logging.getLogger("delete_dir_test")
    caplog.set_level(logging.ERROR, logger=logger.name)
    result = delete_file(str(dir_path), logger)
    assert result is False
    assert any(rec.levelno == logging.ERROR for rec in caplog.records)
    combined_logs = " ".join(rec.getMessage() for rec in caplog.records).lower()
    assert "directory" in combined_logs or "is a directory" in combined_logs


def test_delete_file_empty_path(caplog):
    logger = logging.getLogger("delete_empty_test")
    caplog.set_level(logging.ERROR, logger=logger.name)
    result = delete_file("", logger)
    assert result is False
    assert any(rec.levelno == logging.ERROR for rec in caplog.records)
    combined_logs = " ".join(rec.getMessage() for rec in caplog.records).lower()
    assert "invalid" in combined_logs or "no such file" in combined_logs or "not found" in combined_logs


def test_resolve_path_relative(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative_path = "subfolder/test.txt"
    (tmp_path / "subfolder").mkdir()
    result = resolve_path(relative_path)
    expected_path = tmp_path / "subfolder" / "test.txt"
    assert result == expected_path


def test_resolve_path_absolute_identity(tmp_path):
    absolute = tmp_path / "file.txt"
    result = resolve_path(str(absolute))
    assert isinstance(result, Path)
    assert str(result) == str(absolute)


def test_resolve_path_nonexistent():
    fake_path = "/some/path/that/does/not/exist.txt"
    result = resolve_path(fake_path)
    assert isinstance(result, Path)
    assert str(result) == fake_path or str(result) == os.path.abspath(fake_path)
