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

from dedal.build_cache.BuildCacheManagerOci import BuildCacheManagerOci
from dedal.build_cache.BuildCacheManagerOciDefault import BuildCacheManagerOciDefault
from dedal.configuration.SpackConfig import SpackConfig
from dedal.enum.SpackCacheStorageEnum import SpackCacheStorageEnum


class BuildCacheManagerCreator:
    @staticmethod
    def get_build_cache_manager_operator(spack_config: SpackConfig = SpackConfig()):
        if spack_config.spack_cache_storage_type is SpackCacheStorageEnum.OCI:
            cache_dependency = BuildCacheManagerOci(os.environ.get('CONCRETIZE_OCI_HOST'),
                                                    os.environ.get('CONCRETIZE_OCI_PROJECT'),
                                                    os.environ.get('CONCRETIZE_OCI_USERNAME'),
                                                    os.environ.get('CONCRETIZE_OCI_PASSWORD'),
                                                    cache_version=spack_config.cache_version_concretize)
            build_cache = BuildCacheManagerOci(os.environ.get('BUILDCACHE_OCI_HOST'),
                                               os.environ.get('BUILDCACHE_OCI_PROJECT'),
                                               os.environ.get('BUILDCACHE_OCI_USERNAME'),
                                               os.environ.get('BUILDCACHE_OCI_PASSWORD'),
                                               cache_version=spack_config.cache_version_build)
            return cache_dependency, build_cache
        elif spack_config.spack_cache_storage_type is SpackCacheStorageEnum.OCI_DEFAULT:
            cache_dependency = BuildCacheManagerOciDefault(os.environ.get('CONCRETIZE_OCI_HOST'),
                                                           os.environ.get('CONCRETIZE_OCI_PROJECT'),
                                                           os.environ.get('CONCRETIZE_OCI_USERNAME'),
                                                           os.environ.get('CONCRETIZE_OCI_PASSWORD'),
                                                           cache_version=spack_config.cache_version_concretize)
            build_cache = BuildCacheManagerOciDefault(os.environ.get('BUILDCACHE_OCI_HOST'),
                                                      os.environ.get('BUILDCACHE_OCI_PROJECT'),
                                                      os.environ.get('BUILDCACHE_OCI_USERNAME'),
                                                      os.environ.get('BUILDCACHE_OCI_PASSWORD'),
                                                      cache_version=spack_config.cache_version_build)
            return cache_dependency, build_cache
        return None, None
