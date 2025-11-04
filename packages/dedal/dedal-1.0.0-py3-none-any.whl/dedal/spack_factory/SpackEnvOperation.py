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

import re
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dedal.utils.spack_utils import extract_spack_packages

from dedal.enum.SpackConfigCommand import SpackConfigCommand
from dedal.error_handling.exceptions import BashCommandException, MissingAttributeException, \
    NoSpackEnvironmentException, SpackRepoException, SpackConfigException, SpackFindException, SpackSpecException, \
    SpackFetchException, SpackMergeEnvsException, CreateLoadEnvException, SpackAddException, SpackRemoveException
from dedal.utils.utils import git_clone_repo, run_command, count_files_in_folder
from dedal.logger.logger_builder import get_logger
from dedal.configuration.SpackConfig import SpackConfig


class SpackEnvOperation:
    def __init__(self, spack_config: SpackConfig = SpackConfig(), logger=get_logger(__name__), spack_setup_script=None,
                 env_path=None, spack_command_on_env=None):
        self.spack_config = spack_config
        self.logger = logger
        self.env_path = env_path
        if spack_setup_script and spack_command_on_env:
            self.spack_setup_script = spack_setup_script
            self.spack_command_on_env = spack_command_on_env
        else:
            raise MissingAttributeException(f'Missing attribute for class {__name__}')

    def setup_spack_environment(self):
        """
        Fetches a spack environment if the git path is defined, otherwise creates it. If site-config is defined, it merges the spack.yaml files
        """
        site_config_path = self.env_path / 'site-config'
        if self.spack_config.env and self.spack_config.env.git_path:
            self.logger.info('Setup spack environment: fetch environment from git repo')
            git_clone_repo(self.spack_config.env.name, self.env_path,
                           self.spack_config.env.git_path, self.spack_config.env.git_branch,
                           logger=self.logger)
        elif self.env_path and self.env_path.exists():
            self.logger.info('Setup spack environment: the spack environment is already created and fetched.')
            return
        else:
            os.makedirs(self.env_path, exist_ok=True)
            if self.env_path:
                run_command("bash", "-c",
                            f'{self.spack_setup_script} && spack env create -d {self.env_path}',
                            check=True, logger=self.logger,
                            info_msg=f"Created {self.spack_config.env.name} spack environment",
                            exception_msg=f"Failed to create {self.spack_config.env.name} spack environment",
                            exception=BashCommandException)
                self.logger.info('Setup spack environment: created spack environment')
            else:
                raise MissingAttributeException(f'Missing env_path attribute class {__name__}')

    def merge_envs(self, env_path: Path, site_config_path: Path):
        """
        Merges current environment with the specified environment from site-config
        """
        site_config_dest = self.env_path / 'site-config'
        if site_config_dest.exists():
            shutil.rmtree(site_config_dest)
            os.makedirs(site_config_dest)

        self.logger.debug(f'site-config path: {site_config_path.parent}')
        shutil.copytree(site_config_path.parent.parent, site_config_dest)

        script_dir = Path(__file__).resolve().parent.parent
        y_merge_path = script_dir / 'utils' / 'ymerge.py'
        self.logger.debug(f'Original env path: {env_path}')
        self.logger.debug(f'Additional env path: {site_config_path}')
        # update environment site-configs
        merged_envs = run_command(
            "bash", "-c",
            f'{self.spack_setup_script} && spack-python {y_merge_path} {site_config_path} {env_path}',
            info_msg='Merging top-level and site-specific spack.yaml files.',
            exception_msg='Failed to merge top-level and site-specific spack.yaml files.',
            capture_output=True,
            exception=SpackMergeEnvsException,
            text=True,
            check=True
        )

        tmp_spack_yaml = Path("/tmp/spack.yaml").resolve()
        try:
            with open(tmp_spack_yaml, "w") as f:
                f.write(merged_envs.stdout)
        except Exception as e:
            raise SpackMergeEnvsException(f"Error writing {tmp_spack_yaml}: {e}\n")
        if os.path.exists(self.env_path / 'spack.yaml'):
            os.remove(self.env_path / 'spack.yaml')
        shutil.copy(tmp_spack_yaml, self.env_path)

    def spack_repo_exists(self, repo_name: str) -> bool | None:
        """Check if the given Spack repository exists.
        Returns:
            True if spack repository exists, False otherwise.
        """
        if self.spack_config.env is None:
            result = run_command("bash", "-c",
                                 f'{self.spack_setup_script} && spack repo list',
                                 check=True,
                                 capture_output=True, text=True, logger=self.logger,
                                 info_msg=f'Checking if {repo_name} exists')
            if result is None:
                return False
        else:
            if self.spack_env_exists():
                result = run_command("bash", "-c",
                                     f'{self.spack_command_on_env} && spack repo list',
                                     check=True,
                                     capture_output=True, text=True, logger=self.logger,
                                     info_msg=f'Checking if repository {repo_name} was added').stdout
            else:
                self.logger.debug('No spack environment defined')
                raise NoSpackEnvironmentException('No spack environment defined')
            if result is None:
                return False
        return any(line.strip().endswith(repo_name) for line in result.splitlines())

    def spack_env_exists(self):
        """Checks if a spack environments exists.
        Returns:
            True if spack environments exists, False otherwise.
        """
        result = run_command("bash", "-c",
                             self.spack_command_on_env,
                             check=True,
                             capture_output=True, text=True, logger=self.logger,
                             info_msg=f'Checking if environment {self.spack_config.env.name} exists')
        return result is not None

    def add_spack_repo(self, repo_path: Path, repo_name: str):
        """Add the Spack repository if it does not exist."""
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack repo add {repo_path}/{repo_name}',
                    check=True, logger=self.logger,
                    info_msg=f"Added {repo_name} to spack environment {self.spack_config.env.name}",
                    exception_msg=f"Failed to add {repo_name} to spack environment {self.spack_config.env.name}",
                    exception=SpackRepoException)

    def get_compiler_version(self):
        """Returns the compiler version
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        result = run_command("bash", "-c",
                             f'{self.spack_command_on_env} && spack compiler list',
                             check=True, logger=self.logger,
                             capture_output=True, text=True,
                             info_msg=f"Checking spack environment compiler version for {self.spack_config.env.name}",
                             exception_msg=f"Failed to checking spack environment compiler version for {self.spack_config.env.name}",
                             exception=BashCommandException)

        if result.stdout is None:
            self.logger.debug(f'No gcc found for {self.spack_config.env.name}')
            return None

        # Find the first occurrence of a GCC compiler using regex
        match = re.search(r"gcc@([\d\.]+)", result.stdout)
        gcc_version = match.group(1)
        self.logger.debug(f'Found gcc for {self.spack_config.env.name}: {gcc_version}')
        return gcc_version

    def config(self, config_type: SpackConfigCommand, config_parameter):
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack config {config_type.value} \"{config_parameter}\"',
                    check=True,
                    logger=self.logger,
                    info_msg='Spack config command',
                    exception_msg='Spack config command failed',
                    exception=SpackConfigException)

    def add_package(self, package: str):
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack add {package}"',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Spack add {package} command',
                    exception_msg=f'Spack add  command {package} failed',
                    exception=SpackAddException)

    def remove_package(self, package: str, force: bool = False):
        force = '--force' if force else ''
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack uninstall {force}  {package}"',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Spack remove {package} command',
                    exception_msg=f'Spack remove  command {package} failed',
                    exception=SpackRemoveException)

    def find_packages(self):
        """Returns a dictionary of installed Spack packages in the current environment.
        Each key is the name of a Spack package, and the corresponding value is a list of
        installed versions for that package.
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        packages = run_command("bash", "-c",
                               f'{self.spack_command_on_env} && spack find -c',
                               check=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True,
                               logger=self.logger,
                               info_msg=f'Listing installed packages.',
                               exception_msg=f'Failed to list installed packages',
                               exception=SpackFindException).stdout
        dict_packages = {}
        for package in packages.strip().splitlines():
            line = package.strip()
            if line.startswith(('[+]', '[e]')):
                parts = line.replace('@', ' ').split()
                if len(parts) == 3:
                    _, name, version = parts
                    dict_packages.setdefault(name, []).append(version)
        return dict_packages

    def find_package(self, package, long: bool, variants: bool, paths: bool):
        """
            Searches for a specific packages
        """
        if package is None:
            raise SpackFindException("No package was passed as argument.")

        long = '--long' if long else ''
        variants = '--variants' if variants else ''
        paths = '--paths' if paths else ''
        package = run_command("bash", "-c",
                              f'{self.spack_command_on_env} && spack find {long} {variants} {paths} {package}',
                              check=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True,
                              logger=self.logger,
                              info_msg=f'Finding package {package}',
                              exception_msg=f'Failed find package {package}',
                              exception=SpackFindException).stdout
        return package

    def fetch(self, dependencies=False, missing=False):
        """Spack fetch functionality.
        Raises:
            SpackFetchException: If the spack fails to fetch.
        """
        dependencies = '--dependencies' if dependencies else ''
        missing = '--missing' if missing else ''
        result = run_command("bash", "-c",
                             f'{self.spack_command_on_env} && spack fetch {dependencies} {missing}',
                             check=True, logger=self.logger,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             capture_output=True,
                             text=True,
                             info_msg=f"Checking spack environment compiler version for {self.spack_config.env.name}",
                             exception_msg=f"Failed to checking spack environment compiler version for {self.spack_config.env.name}",
                             exception=SpackFetchException)
        return result

    def spec_pacakge(self, package_name: str, full_format=False):
        """Spec step for a spack environment
            Raises:
                SpackSpecException: If the spack spec command fails.
        """
        try:
            spec_output = run_command("bash", "-c",
                                      f'{self.spack_command_on_env} && spack spec {package_name}',
                                      check=True,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      text=True,
                                      logger=self.logger,
                                      info_msg=f'Spack spec {package_name}.',
                                      exception_msg=f'Failed to spack spec {package_name}.',
                                      exception=SpackSpecException).stdout
            if full_format:
                return spec_output
            else:
                pattern = r'^\s*-\s*([\w.-]+@[\d.]+)'
                match = re.search(pattern, spec_output)
                if match:
                    return match.group(1)
                return None
        except SpackSpecException:
            return None

    def check_installed_spack_packages(self, env_path: Path):
        """
            Checks if all spack packages from the environment (spack.yaml) were installed successfully.
         """
        to_install = extract_spack_packages(env_path / 'spack.yaml')
        installed = self.find_packages()
        installed = list(installed.keys())
        for package in to_install:
            if package not in installed:
                return False
        return True

    def create_load_env_script(self):
        """
            Creates load script that when sourced activates and loads the installed spack environment, using views
        """
        with open(self.env_path / 'load_env.sh', "w") as load_env:
            run_command("bash", "-c",
                        f'{self.spack_setup_script} && spack env activate --sh {self.env_path}',
                        check=True,
                        stdout=load_env,
                        stderr=subprocess.PIPE,
                        exception=CreateLoadEnvException,
                        text=True,
                        )

    def spack_clean(self, bootstrap: bool = False):
        bootstrap = '--bootstrap' if bootstrap else ''
        run_command("bash", "-c",
                    f'{self.spack_setup_script} && spack clean -a {bootstrap}',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Spack clean command',
                    exception_msg=f'Spack failed to clean command failed',
                    exception=SpackRemoveException)
