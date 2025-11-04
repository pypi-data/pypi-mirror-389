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
from pathlib import Path

from dedal.build_cache.BuildCacheManagerCreator import BuildCacheManagerCreator
from dedal.configuration.SpackConfig import SpackConfig
from dedal.error_handling.exceptions import SpackInstallPackagesException
from dedal.logger.logger_builder import get_logger
from dedal.spack_factory.SpackOperation import SpackOperation
from dedal.utils.utils import file_exists_and_not_empty, run_command, log_command, copy_file
from dedal.wrapper.spack_wrapper import check_spack_env


class SpackOperationUseCache(SpackOperation):
    """
    This class uses caching for the concretization step and for the installation step.
    """

    def __init__(self, spack_config: SpackConfig = SpackConfig()):
        super().__init__(spack_config, logger=get_logger(__name__))
        self.signed = False
        self.cache_dependency, self.build_cache = BuildCacheManagerCreator.get_build_cache_manager_operator(
            spack_config)

    def setup_spack_env(self) -> None:
        """Set up the spack environment for using the cache.
        Downloads the build cache, adds the public key to trusted keys,
        and adds the build cache mirror.
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        super().setup_spack_env()
        # Download concretization cache from OCI Registry
        if self.cache_dependency:
            self.cache_dependency.download(self.spack_config.concretization_dir)
        # Download build cache from OCI Registry and add public key to trusted keys
        if self.build_cache:
            self.build_cache.download(self.spack_config.buildcache_dir)
            cached_public_key = self.build_cache.get_public_key_from_cache(str(self.spack_config.buildcache_dir))
            self.signed = cached_public_key is not None
            if self.signed:
                self.trust_gpg_key(cached_public_key)
            # Add build cache mirror
            self.add_mirror('local_cache',
                            str(self.spack_config.buildcache_dir),
                            signed=self.signed,
                            autopush=False,
                            global_mirror=False)
            self.update_buildcache_index(self.spack_config.buildcache_dir)
            self.install_gpg_keys()

    @check_spack_env
    def concretize_spack_env(self, test=None):
        """Concretization step for spack environment for using the concretization cache (spack.lock file).
        Downloads the concretization cache and moves it to the spack environment's folder
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        concretization_redo = False
        if self.cache_dependency and file_exists_and_not_empty(self.spack_config.concretization_dir / 'spack.lock'):
            concretization_file_path = self.env_path / 'spack.lock'
            copy_file(self.spack_config.concretization_dir / 'spack.lock', self.env_path)
            # redo the concretization step if spack.lock file was not downloaded from the cache
            if not file_exists_and_not_empty(concretization_file_path):
                super().concretize_spack_env(force=True, test=test)
                concretization_redo = True
        else:
            # redo the concretization step if spack.lock file was not downloaded from the cache
            super().concretize_spack_env(force=True, test=test)
            concretization_redo = True
        if concretization_redo is True:
            self.logger.info(f'Redo of concretization step.')
        else:
            self.logger.info(f'Used concretization from cache.')
        return concretization_redo

    @check_spack_env
    def install_packages(self, jobs: int, debug=False, test=None):
        """Installation step for spack environment for using the binary caches.

        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        signed = '' if self.signed else '--no-check-signature'
        debug = '--debug' if debug else ''
        test = f'--test {test}' if test else ''
        if self.build_cache:
            install_result = run_command("bash", "-c",
                                         f'{self.spack_command_on_env} && spack {debug} install {signed} -j {jobs} {test}',
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True,
                                         logger=self.logger,
                                         info_msg=f"Installing spack packages for {self.spack_config.env.name}",
                                         exception_msg=f"Error installing spack packages for {self.spack_config.env.name}",
                                         exception=SpackInstallPackagesException)
            log_command(install_result, str(Path(os.getcwd()).resolve() / ".generate_cache.log"))
            if install_result.returncode == 0:
                self.logger.info(f'Finished installation of spack packages from cache.')
            else:
                self.logger.error(f'Something went wrong during installation from cache. Please check the logs.')
        else:
            install_result = super().install_packages(jobs=jobs, signed=signed, debug=debug, test=test)
        return install_result
