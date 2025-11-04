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

from dedal.build_cache.BuildCacheManagerCreator import BuildCacheManagerCreator
from dedal.utils.utils import copy_file
from dedal.wrapper.spack_wrapper import check_spack_env
from dedal.configuration.SpackConfig import SpackConfig
from dedal.logger.logger_builder import get_logger
from dedal.spack_factory.SpackOperation import SpackOperation


class SpackOperationCreateCache(SpackOperation):
    """
    This class creates caching for the concretization step and for the installation step.
    """

    def __init__(self, spack_config: SpackConfig = SpackConfig()):
        super().__init__(spack_config, logger=get_logger(__name__))
        self.cache_dependency, self.build_cache = BuildCacheManagerCreator.get_build_cache_manager_operator(
            spack_config)
        self.signed = False
        if self.spack_config.gpg:
            self.signed = True

    def setup_spack_env(self) -> None:
        """Set up the spack environment for creating the cache.
        Creates the caching for the concretization and install steps and then uploads them to the OCI registry.
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        super().setup_spack_env()
        if self.signed:
            self.create_gpg_keys()
            self.logger.info('Created gpg keys')
        self.add_mirror('local_cache',
                        str(self.spack_config.buildcache_dir),
                        signed=self.signed,
                        autopush=True,
                        global_mirror=False)
        self.logger.info(f'Added mirror for {self.spack_config.env.name}')

    @check_spack_env
    def concretize_spack_env(self, test=None):
        """Concretization step for a spack environment. After the concretization step is complete, the concretization file is uploaded to the OCI casing.
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        super().concretize_spack_env(force=True, test=test)
        if self.cache_dependency:
            dependency_path = self.spack_config.env.path / self.spack_config.env.name / 'spack.lock'
            copy_file(dependency_path, self.spack_config.concretization_dir, logger=self.logger)
            self.cache_dependency.upload(self.spack_config.concretization_dir,
                                         override_cache=self.spack_config.override_cache)
            self.logger.info(
                f'Finished uploading new spack concretization for create cache: {self.spack_config.env.name}')
        else:
            self.logger.info(
                f'Created new spack concretization for create cache: {self.spack_config.env.name}. No OCI credentials for concretization step were provided!')

    @check_spack_env
    def install_packages(self, jobs: int = 2, debug=False, test=None):
        """Installs all spack packages. After the installation is complete, all the binary cashes are pushed to the defined OCI registry
        Raises:
            NoSpackEnvironmentException: If the spack environment is not set up.
        """
        super().install_packages(jobs=jobs, signed=self.signed, debug=debug, fresh=True, test=test)
        if self.build_cache:
            self.build_cache.upload(self.spack_config.buildcache_dir, override_cache=self.spack_config.override_cache)
            self.logger.info(f'Finished uploading build cache: {self.spack_config.env.name}')
        else:
            self.logger.info(
                f'Created build cache: {self.spack_config.env.name}. No OCI credentials for concretization step were provided!')
