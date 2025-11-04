# Dedal library - Wrapper over Spack for building multiple target
# environments: ESD, Virtual Boxes, HPC compatible kernels, etc.
import errno
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
import shutil
import subprocess
import tempfile
from pathlib import Path

from oras.logger import Logger

from dedal.error_handling.exceptions import BashCommandException
import re


def clean_up(dirs: list[str], logger: logging = logging.getLogger(__name__), ignore_errors=True):
    """
        All the folders from the list dirs are removed with all the content in them
    """
    for cleanup_dir in dirs:
        cleanup_dir = Path(cleanup_dir).resolve()
        if cleanup_dir.exists():
            logger.info(f"Removing {cleanup_dir}")
            try:
                shutil.rmtree(Path(cleanup_dir))
            except OSError as e:
                logger.error(f"Failed to remove {cleanup_dir}: {e}")
                if not ignore_errors:
                    raise e
        else:
            logger.info(f"{cleanup_dir} does not exist")


def run_command(*args, logger=logging.getLogger(__name__), info_msg: str = '', exception_msg: str = None,
                exception=None, **kwargs):
    try:
        logger.info(f'{info_msg}: args: {args}')
        return subprocess.run(args, **kwargs)
    except subprocess.CalledProcessError as e:
        if exception_msg is not None:
            logger.error(f"{exception_msg}: {e}")
        if exception is not None:
            raise exception(f'{exception_msg} : {e}')
        else:
            return None
    except FileNotFoundError:
        logger.error(f"Command not found. Please check the command syntax.")
    except PermissionError:
        logger.error(f"Permission denied. Try running with appropriate permissions.")
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out. Try increasing the timeout duration.")
    except ValueError:
        logger.error(f"Invalid argument passed to subprocess. Check function parameters.")
    except OSError as e:
        logger.error(f"OS error occurred: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
    return None


def git_clone_repo(repo_name: str, dir: Path, git_path: str, git_branch: str = '',
                   logger: Logger = logging.getLogger(__name__)):
    if not dir.exists():
        run_command(
            'git', f'clone', '--depth', '1',
            '-c', 'advice.detachedHead=false',
            '-c', 'feature.manyFiles=true',
            *(['-b', git_branch] if git_branch else []),
            git_path, dir
            , check=True, logger=logger,
            exception_msg=f'Failed to clone repository: {repo_name}',
            exception=BashCommandException)
    else:
        logger.info(f'Repository {repo_name} already cloned.')


def file_exists_and_not_empty(file: Path) -> bool:
    return file.is_file() and file.stat().st_size > 0


def log_command(results, log_file: str):
    try:
        with open(log_file, "w") as log_file:
            log_file.write(results.stdout)
            log_file.write("\n--- STDERR ---\n")
            log_file.write(results.stderr)
    except OSError as e:
        if e.errno == errno.ENOSPC:
            print(f"ERROR: No space left on device when writing")
        else:
            raise


def copy_to_tmp(file_path: Path) -> Path:
    """
    Creates a temporary directory and copies the given file into it.

    :param file_path: Path to the file that needs to be copied.
    :return: Path to the copied file inside the temporary directory.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    tmp_dir = Path(tempfile.mkdtemp())
    tmp_file_path = tmp_dir / file_path.name
    shutil.copy(file_path, tmp_file_path)
    return tmp_file_path


def set_bashrc_variable(var_name: str, value: str, bashrc_path: str = os.path.expanduser("~/.bashrc"),
                        logger: logging = logging.getLogger(__name__), update_variable=False):
    """Update or add an environment variable in ~/.bashrc."""
    if bashrc_path is None or var_name is None or value is None:
        return
    value = value.replace("$", r"\$")
    with open(bashrc_path, "r") as file:
        lines = file.readlines()
    pattern = re.compile(rf'^\s*export\s+{var_name}=.*$')
    found_variable = False
    # Modify the existing variable if found
    for i, line in enumerate(lines):
        if pattern.match(line):
            if update_variable:
                lines[i] = f'export {var_name}={value}\n'
            found_variable = True
            break
    if not found_variable:
        lines.append(f'\nexport {var_name}={value}\n')
        logger.info(f"Added in {bashrc_path} with: export {var_name}={value}")
    else:
        logger.info(f"Updated {bashrc_path} with: export {var_name}={value}")
    with open(bashrc_path, "w") as file:
        file.writelines(lines)


def copy_file(src: Path, dst: Path, logger: logging = logging.getLogger(__name__)) -> None:
    """
    Copy a file from src to dest.
    """
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source file '{src}' does not exist.")
    src.resolve().as_posix()
    dst.resolve().as_posix()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    logger.debug(f"File copied from '{src}' to '{dst}'")


def delete_file(file_path: str, logger: logging = logging.getLogger(__name__)) -> bool:
    """
    Deletes a file at the given path. Returns True if successful, False if the file doesn't exist.
    """
    try:
        os.remove(file_path)
        logger.debug(f"File '{file_path}' deleted.")
        return True
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return False
    except PermissionError:
        logger.error(f"Permission denied: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
        return False


def resolve_path(path: str):
    if path is None:
        path = Path(os.getcwd()).resolve()
    else:
        path = Path(path).resolve()
    return path


def count_files_in_folder(folder_path: Path) -> int:
    if not folder_path.is_dir():
        return 0
    return sum(1 for sub_path in folder_path.rglob("*") if sub_path.is_file())


def get_first_word(s: str) -> str:
    return s.split()[0] if s.strip() else ''
