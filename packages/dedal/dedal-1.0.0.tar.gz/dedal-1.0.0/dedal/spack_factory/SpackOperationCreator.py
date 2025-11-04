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

from dedal.configuration.SpackConfig import SpackConfig
from dedal.spack_factory.SpackOperation import SpackOperation
from dedal.spack_factory.SpackOperationCreateCache import SpackOperationCreateCache
from dedal.spack_factory.SpackOperationUseCache import SpackOperationUseCache


class SpackOperationCreator:
    @staticmethod
    def get_spack_operator(spack_config: SpackConfig = None, use_cache: bool = False) -> SpackOperation:
        env_vars_concretization_cache = [
            os.environ.get('CONCRETIZE_OCI_HOST'),
            os.environ.get('CONCRETIZE_OCI_PROJECT'),
            os.environ.get('CONCRETIZE_OCI_USERNAME'),
            os.environ.get('CONCRETIZE_OCI_PASSWORD'),
        ]
        env_vars_build_cache = [
            os.environ.get('BUILDCACHE_OCI_HOST'),
            os.environ.get('BUILDCACHE_OCI_PROJECT'),
            os.environ.get('BUILDCACHE_OCI_USERNAME'),
            os.environ.get('BUILDCACHE_OCI_PASSWORD')
        ]
        if spack_config is None:
            return SpackOperation()
        elif None in env_vars_concretization_cache and None in env_vars_build_cache:
            return SpackOperation(spack_config)
        elif spack_config.concretization_dir is None and spack_config.buildcache_dir is None:
            return SpackOperation(spack_config)
        elif (spack_config.concretization_dir or spack_config.buildcache_dir) and not use_cache:
            return SpackOperationCreateCache(spack_config)
        elif (spack_config.concretization_dir or spack_config.buildcache_dir) and use_cache:
            return SpackOperationUseCache(spack_config)
        else:
            return SpackOperation(SpackConfig())
