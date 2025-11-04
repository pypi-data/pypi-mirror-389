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
from pathlib import Path
from dedal.configuration.GpgConfig import GpgConfig
from dedal.enum.SpackCacheStorageEnum import SpackCacheStorageEnum
from dedal.enum.SpackViewEnum import SpackViewEnum
from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.utils.utils import resolve_path


class SpackConfig:
    def __init__(self, env: SpackDescriptor = None, repos: list[SpackDescriptor] = None,
                 install_dir=Path(os.getcwd()).resolve(), upstream_instance=None, system_name=None,
                 concretization_dir: Path = None, buildcache_dir: Path = None, gpg: GpgConfig = None,
                 use_spack_global=False, cache_version_concretize='v1',
                 cache_version_build='v1', view=SpackViewEnum.VIEW, override_cache=True, bashrc_path=os.path.expanduser("~/.bashrc"),
                 spack_cache_storage_type: SpackCacheStorageEnum = SpackCacheStorageEnum.OCI,
                 spack_dir: Path = None, serialize_name: str = 'data.pkl'):
        self.env = env
        self.serialize_name = serialize_name
        if repos is None:
            self.repos = []
        else:
            self.repos = repos
        self.spack_dir = spack_dir
        self.upstream_instance = upstream_instance
        self.system_name = system_name
        self.concretization_dir = concretization_dir if concretization_dir is None else resolve_path(concretization_dir)
        self.buildcache_dir = buildcache_dir if buildcache_dir is None else resolve_path(buildcache_dir)
        self.install_dir = resolve_path(install_dir)
        self.gpg = gpg
        self.use_spack_global = use_spack_global
        self.cache_version_concretize = cache_version_concretize
        self.cache_version_build = cache_version_build
        self.view = view
        self.override_cache = override_cache
        self.bashrc_path = bashrc_path
        self.spack_cache_storage_type = spack_cache_storage_type

    def add_repo(self, repo: SpackDescriptor):
        if self.repos is None:
            self.repos = []
        else:
            self.repos.append(repo)
