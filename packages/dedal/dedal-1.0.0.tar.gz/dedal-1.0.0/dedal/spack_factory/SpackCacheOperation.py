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

import subprocess
from pathlib import Path

from dedal.utils.utils import run_command, get_first_word

from dedal.wrapper.spack_wrapper import check_spack_env

from dedal.error_handling.exceptions import MissingAttributeException, SpackGpgException, SpackMirrorException, \
    SpackReindexException, SpackCreateBuildCacheException
from dedal.logger.logger_builder import get_logger

from dedal.configuration.SpackConfig import SpackConfig


class SpackCacheOperation:
    def __init__(self, spack_config: SpackConfig = SpackConfig(), logger=get_logger(__name__), spack_setup_script=None,
                 spack_dir=Path('./').resolve(), spack_command_on_env=None):
        self.spack_config = spack_config
        self.logger = logger
        if spack_setup_script and spack_command_on_env:
            self.spack_setup_script = spack_setup_script
            self.spack_command_on_env = spack_command_on_env
        else:
            raise MissingAttributeException(f'Missing attribute for class {__name__}')
        self.spack_dir = spack_dir

    def add_mirror(self, mirror_name: str, mirror_path: Path, signed=False, autopush=False, global_mirror=False):
        """Adds a Spack mirror.
        Adds a new mirror to the Spack configuration, either globally or to a specific environment.
        Args:
            mirror_name (str): The name of the mirror.
            mirror_path (str): The path or URL of the mirror.
            signed (bool): Whether to require signed packages from the mirror.
            autopush (bool): Whether to enable autopush for the mirror.
            global_mirror (bool): Whether to add the mirror globally (True) or to the current environment (False).
        Raises:
            ValueError: If mirror_name or mirror_path are empty.
            NoSpackEnvironmentException: If global_mirror is False and no environment is defined.
        """
        autopush = '--autopush' if autopush else ''
        signed = '--signed' if signed else '--unsigned'
        spack_add_mirror = f'spack mirror add {autopush} {signed} {mirror_name} {mirror_path}'
        if global_mirror:
            run_command("bash", "-c",
                        f'{self.spack_setup_script} && {spack_add_mirror}',
                        check=True,
                        logger=self.logger,
                        info_msg=f'Added mirror {mirror_name}',
                        exception_msg=f'Failed to add mirror {mirror_name}',
                        exception=SpackMirrorException)
        else:
            check_spack_env(
                run_command("bash", "-c",
                            f'{self.spack_command_on_env} && {spack_add_mirror}',
                            check=True,
                            logger=self.logger,
                            info_msg=f'Added mirror {mirror_name}',
                            exception_msg=f'Failed to add mirror {mirror_name}',
                            exception=SpackMirrorException))

    def trust_gpg_key(self, public_key_path: str):
        """Adds a GPG public key to the trusted keyring.
        This method attempts to add the provided GPG public key to the
        Spack trusted keyring.
        Args:
            public_key_path (str): Path to the GPG public key file.
        Returns:
            bool: True if the key was added successfully, False otherwise.
        Raises:
            ValueError: If public_key_path is empty.
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        if not public_key_path:
            raise ValueError("public_key_path is required")

        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack gpg trust {public_key_path}',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Trusted GPG key for {self.spack_config.env.name}',
                    exception_msg=f'Failed to trust GPG key for {self.spack_config.env.name}',
                    exception=SpackGpgException)

    def mirror_list(self):
        """Returns of available mirrors. When an environment is activated it will return the mirrors associated with it,
           otherwise the mirrors set globally"""
        mirrors = run_command("bash", "-c",
                              f'{self.spack_command_on_env} && spack mirror list',
                              check=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              text=True,
                              logger=self.logger,
                              info_msg=f'Listing mirrors',
                              exception_msg=f'Failed list mirrors',
                              exception=SpackMirrorException).stdout
        return list(map(get_first_word, list(mirrors.strip().splitlines())))

    def remove_mirror(self, mirror_name: str):
        """Removes a mirror from an environment (if it is activated), otherwise removes the mirror globally."""
        if not mirror_name:
            raise ValueError("mirror_name is required")
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack mirror rm {mirror_name}',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Removing mirror {mirror_name}',
                    exception_msg=f'Failed to remove mirror {mirror_name}',
                    exception=SpackMirrorException)

    def update_buildcache_index(self, mirror_path: str):
        """Updates buildcache index"""
        if not mirror_path:
            raise ValueError("mirror_path is required")
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack buildcache update-index {mirror_path}',
                    # check=True,
                    logger=self.logger,
                    info_msg=f'Updating build cache index for mirror {mirror_path}',
                    exception_msg=f'Failed to update build cache index for mirror {mirror_path}',
                    exception=SpackMirrorException)

    def install_gpg_keys(self):
        """Install gpg keys"""
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack buildcache keys --install --trust',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Installing gpg keys from mirror',
                    exception_msg=f'Failed to install gpg keys from mirror',
                    exception=SpackGpgException)

    def create_gpg_keys(self):
        """Creates GPG keys (which can be used when creating binary cashes) and adds it to the trusted keyring."""
        if self.spack_config.gpg:
            run_command("bash", "-c",
                        f'{self.spack_setup_script} && spack gpg init && spack gpg create {self.spack_config.gpg.name} {self.spack_config.gpg.mail}',
                        check=True,
                        logger=self.logger,
                        info_msg=f'Created pgp keys for {self.spack_config.env.name}',
                        exception_msg=f'Failed to create pgp keys mirror {self.spack_config.env.name}',
                        exception=SpackGpgException)
        else:
            raise SpackGpgException('No GPG configuration was defined is spack configuration')

    def reindex(self):
        """
            Reindex step for a spack environment
            Raises:
                SpackReindexException: If the spack reindex command fails.
        """
        run_command("bash", "-c",
                    f'{self.spack_command_on_env} && spack reindex',
                    check=True,
                    logger=self.logger,
                    info_msg=f'Reindex step.',
                    exception_msg=f'Failed the reindex.',
                    exception=SpackReindexException)

    def create_build_cache(self, package=None, unsigned=True, only=False):
        """
            Created build cache for a specific spack package.
            Raises:
                SpackCreateBuildCacheException: If the spack create buildcache fails.
        """
        unsigned = '--unsigned' if unsigned else ''
        only = '--only' if only else ''
        result = run_command("bash", "-c",
                                     f'{self.spack_command_on_env} && spack buildcache create {unsigned} {only} {package}',
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     text=True,
                                     logger=self.logger,
                                     info_msg=f"Created buildcache for pakcage {package}",
                                     exception_msg=f"Error creating buildcache for package {package}",
                                     exception=SpackCreateBuildCacheException)
        return result.returncode