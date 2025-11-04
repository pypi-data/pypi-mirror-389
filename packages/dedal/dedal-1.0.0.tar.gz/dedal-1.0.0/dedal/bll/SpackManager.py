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
from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.spack_factory.SpackOperationCreator import SpackOperationCreator
from dedal.configuration.SpackConfig import SpackConfig


class SpackManager:
    """
    This class defines the logic used by the CLI
    """

    def __init__(self, spack_config: SpackConfig = None, use_cache=False):
        self._spack_config = spack_config
        self._use_cache = use_cache

    def _get_spack_operation(self):
        return SpackOperationCreator.get_spack_operator(self._spack_config, self._use_cache)

    def install_spack(self, version: str, bashrc_path=os.path.expanduser("~/.bashrc")):
        self._get_spack_operation().install_spack(spack_version=f'{version}', bashrc_path=bashrc_path)

    def add_spack_repo(self, repo: SpackDescriptor):
        """
        After additional repo was added, setup_spack_env must be invoked
        """
        self._spack_config.add_repo(repo)

    def setup_spack_env(self):
        self._get_spack_operation().setup_spack_env()

    def concretize_spack_env(self):
        self._get_spack_operation().concretize_spack_env()

    def install_packages(self, jobs: int):
        self._get_spack_operation().install_packages(jobs=jobs)
