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

import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from dedal.configuration.SpackConfig import SpackConfig
from dedal.enum.SpackConfigCommand import SpackConfigCommand
from dedal.error_handling.exceptions import SpackInstallPackagesException, SpackConcertizeException
from dedal.logger.logger_builder import get_logger
from dedal.serialize.PickleSerializer import PickleSerializer
from dedal.spack_factory.SpackCacheOperation import SpackCacheOperation
from dedal.spack_factory.SpackEnvOperation import SpackEnvOperation
from dedal.spack_factory.SpackToolOperation import SpackToolOperation
from dedal.tests.testing_variables import SPACK_VERSION
from dedal.utils.utils import run_command, git_clone_repo, log_command, set_bashrc_variable
from dedal.wrapper.spack_wrapper import check_spack_env


class SpackOperation:
    """
    This class should implement the methods necessary for installing spack, set up an environment, concretize and install packages.
    Factory design pattern is used because there are 2 cases: creating an environment from scratch or creating an environment from the buildcache.

    Attributes:
    -----------
    env : SpackDescriptor
        spack environment details
    repos : list[SpackDescriptor]
    upstream_instance : str
        path to Spack instance to use as upstream (optional)
    """

    def __init__(self, spack_config: SpackConfig = SpackConfig(), logger=get_logger(__name__)):
        self.spack_config = spack_config
        self.logger = logger
        self.spack_config.install_dir = spack_config.install_dir
        os.makedirs(self.spack_config.install_dir, exist_ok=True)
        if self.spack_config.spack_dir is None:
            self.spack_config.spack_dir = self.spack_config.install_dir / 'spack'
        self.env_path = None
        self.spack_setup_script = "" if self.spack_config.use_spack_global else f"source {self.spack_config.spack_dir / 'share' / 'spack' / 'setup-env.sh'}"
        self.spack_config.concretization_dir = spack_config.concretization_dir
        if self.spack_config.concretization_dir:
            os.makedirs(self.spack_config.concretization_dir, exist_ok=True)
        self.spack_config.buildcache_dir = spack_config.buildcache_dir
        if self.spack_config.buildcache_dir:
            os.makedirs(self.spack_config.buildcache_dir, exist_ok=True)
        if self.spack_config.env and spack_config.env.name:
            self.env_path: Path = spack_config.env.path / spack_config.env.name
            if self.spack_setup_script != "":
                self.spack_command_on_env = f'{self.spack_setup_script} && spack env activate -p {spack_config.view.value} {self.env_path}'
            else:
                self.spack_command_on_env = f'spack env activate -p {spack_config.view.value} {self.env_path}'
        else:
            self.spack_command_on_env = self.spack_setup_script
        if self.spack_config.env and spack_config.env.path:
            self.spack_config.env.path.mkdir(parents=True, exist_ok=True)
        self.spack_tool_operation = SpackToolOperation(spack_config=spack_config,
                                                       spack_setup_script=self.spack_setup_script,
                                                       spack_dir=self.spack_config.spack_dir)
        self.spack_env_operation = SpackEnvOperation(spack_config=spack_config,
                                                     spack_setup_script=self.spack_setup_script,
                                                     env_path=self.env_path,
                                                     spack_command_on_env=self.spack_command_on_env)
        self.spack_cache_operation = SpackCacheOperation(spack_config=spack_config,
                                                         spack_setup_script=self.spack_setup_script,
                                                         spack_command_on_env=self.spack_command_on_env,
                                                         spack_dir=self.spack_config.spack_dir)
        self.serializer = PickleSerializer(file_path=self.spack_config.install_dir,
                                           file_name=self.spack_config.serialize_name)

    def setup_spack_env(self):
        """
        This method prepares a spack environment by fetching/creating the spack environment and adding the necessary repos
        """
        if self.spack_config.system_name:
            set_bashrc_variable('SYSTEMNAME', self.spack_config.system_name, self.spack_config.bashrc_path,
                                logger=self.logger)
            os.environ['SYSTEMNAME'] = self.spack_config.system_name
        if self.spack_config.spack_dir.exists() and self.spack_config.spack_dir.is_dir():
            set_bashrc_variable('SPACK_USER_CACHE_PATH', str(self.spack_config.spack_dir / ".spack"),
                                self.spack_config.bashrc_path,

                                logger=self.logger)
            set_bashrc_variable('SPACK_USER_CONFIG_PATH', str(self.spack_config.spack_dir / ".spack"),
                                self.spack_config.bashrc_path,
                                logger=self.logger)
            self.logger.debug('Added env variables SPACK_USER_CACHE_PATH and SPACK_USER_CONFIG_PATH')
        else:
            self.logger.error(f'Invalid installation path: {self.spack_config.spack_dir}')
        # Restart the bash after adding environment variables
        if self.spack_config.env:
            self.spack_env_operation.setup_spack_environment()
        if self.spack_config.install_dir.exists():
            for repo in self.spack_config.repos:
                repo_dir = self.spack_config.install_dir / repo.path / repo.name
                git_clone_repo(repo.name, repo_dir, repo.git_path, logger=self.logger, git_branch=repo.git_branch)
                if not self.spack_repo_exists(repo.name):
                    self.add_spack_repo(repo.path, repo.name)
                    self.logger.debug(f'Added spack repository {repo.name}')
                else:
                    self.logger.debug(f'Spack repository {repo.name} already added')

    @check_spack_env
    def concretize_spack_env(self, force=True, fresh=False, test=None):
        """Concretization step for a spack environment
            Args:
                force (bool): TOverrides an existing concretization when set to True
                test: which test dependencies should be included
            Raises:
                NoSpackEnvironmentException: If the spack environment is not set up.
        """
        force = '--force' if force else ''
        fresh = '--fresh' if fresh else ''
        test = f'--test {test}' if test else ''
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack concretize {fresh} {force} {test}',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Concertization step for {self.spack_config.env.name}',
                    exception_msg=f'Failed the concertization step for {self.spack_config.env.name}',
                    exception=SpackConcertizeException)

    @check_spack_env
    def install_packages(self, jobs: int, signed=True, fresh=False, debug=False, test=None):
        """Installs all spack packages.
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        signed = '' if signed else '--no-check-signature'
        fresh = '--fresh' if fresh else ''
        debug = '--debug' if debug else ''
        test = f'--test {test}' if test else ''
        install_result = run_command("bash", "-c",
                                     f'{self.spack_command_on_env} && spack {debug} install {signed} -j {jobs} {fresh} {test}',
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     logger=self.logger,
                                     info_msg=f"Installing spack packages for {self.spack_config.env.name}",
                                     exception_msg=f"Error installing spack packages for {self.spack_config.env.name}",
                                     exception=SpackInstallPackagesException)
        log_command(install_result, str(Path(os.getcwd()).resolve() / ".generate_cache.log"))
        if install_result.returncode == 0:
            self.logger.info(f'Finished installation of spack packages from scratch')
        else:
            self.logger.error(f'Something went wrong during installation. Please check the logs.')
        return install_result

    def create_fetch_spack_environment(self):
        self.spack_env_operation.setup_spack_environment()

    def add_spack_repo(self, repo_path: Path, repo_name: str):
        self.spack_env_operation.add_spack_repo(repo_path, repo_name)

    def spack_repo_exists(self, repo_name: str) -> bool | None:
        return self.spack_env_operation.spack_repo_exists(repo_name)

    def spack_env_exists(self):
        return self.spack_env_operation.spack_env_exists()

    @check_spack_env
    def get_compiler_version(self):
        return self.spack_env_operation.get_compiler_version()

    def get_spack_installed_version(self):
        return self.spack_tool_operation.get_spack_installed_version()

    def reindex(self):
        self.spack_cache_operation.reindex()

    def spec_pacakge(self, package_name: str, full_format=False):
        return self.spack_env_operation.spec_pacakge(package_name, full_format)

    def create_gpg_keys(self):
        self.spack_cache_operation.create_gpg_keys()

    def add_mirror(self, mirror_name: str, mirror_path: Path, signed=False, autopush=False, global_mirror=False):
        return self.spack_cache_operation.add_mirror(mirror_name, mirror_path, signed, autopush, global_mirror)

    @check_spack_env
    def trust_gpg_key(self, public_key_path: str):
        self.spack_cache_operation.trust_gpg_key(public_key_path)

    def config(self, config_type: SpackConfigCommand, config_parameter):
        self.spack_env_operation.config(config_type, config_parameter)

    def mirror_list(self):
        return self.spack_cache_operation.mirror_list()

    def remove_mirror(self, mirror_name: str):
        self.spack_cache_operation.remove_mirror(mirror_name)

    def update_buildcache_index(self, mirror_path: str):
        self.spack_cache_operation.update_buildcache_index(mirror_path)

    def install_gpg_keys(self):
        self.spack_cache_operation.install_gpg_keys()

    @check_spack_env
    def find_packages(self):
        return self.spack_env_operation.find_packages()

    def find_package(self, package, long: bool, variants: bool, paths: bool):
        return self.spack_env_operation.find_package(package, long, variants, paths)

    def fetch(self, dependencies=False, missing=False):
        return self.spack_env_operation.fetch(dependencies, missing)

    def install_spack(self, spack_version=f'{SPACK_VERSION}', spack_repo='https://github.com/spack/spack',
                      bashrc_path=os.path.expanduser("~/.bashrc")):
        self.spack_tool_operation.install_spack(spack_version, spack_repo, bashrc_path)

    def check_installed_spack_packages(self, env_path: Path):
        return self.spack_env_operation.check_installed_spack_packages(env_path)

    def create_build_cache(self, package=None, unsigned=True, only=False):
        return self.spack_cache_operation.create_build_cache(package, unsigned, only)

    def serialize(self) -> None:
        """
        Serialize spack configuration to the given file path.
        """
        self.serializer.serialize(self)

    @classmethod
    def deserialize(cls, file_location: Path, file_name: str) -> Any:
        return PickleSerializer(file_location.resolve(), file_name).deserialize()

    def merge_envs(self, env_path: Path, site_config_path: Path):
        return self.spack_env_operation.merge_envs(env_path, site_config_path)

    def create_load_env_script(self):
        self.spack_env_operation.create_load_env_script()

    def add_package(self, package: str):
        self.spack_env_operation.add_package(package)

    def remove_package(self, package: str, force: bool = False):
        self.spack_env_operation.remove_package(package, force)

    def spack_clean(self, bootstrap: bool = False):
        self.spack_env_operation.spack_clean(bootstrap)
