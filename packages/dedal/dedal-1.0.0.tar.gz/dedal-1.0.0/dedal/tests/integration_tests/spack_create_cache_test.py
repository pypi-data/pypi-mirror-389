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

from pathlib import Path

import pytest

from dedal.configuration.GpgConfig import GpgConfig
from dedal.configuration.SpackConfig import SpackConfig

from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.spack_factory.SpackOperationCreateCache import SpackOperationCreateCache
from dedal.spack_factory.SpackOperationCreator import SpackOperationCreator
from dedal.tests.testing_variables import test_spack_env_git, ebrains_spack_builds_git

"""
Before running those tests, the repositories where the caching is stored must be cleared after each run. 
Ebrains Harbour does not support deletion via API, so the clean up must be done manually
"""


def setup(path):
    install_dir = path
    env_name = 'test-spack-env'
    env_path = install_dir / env_name
    concretization_dir = install_dir / 'concretization'
    buildcache_dir = install_dir / 'buildcache'
    env = SpackDescriptor(env_name, install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    config = SpackConfig(env=env, install_dir=install_dir, concretization_dir=concretization_dir,
                         buildcache_dir=buildcache_dir, gpg=None)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    return spack_operation, env_path


@pytest.mark.skip(
    reason="Skipping until an OCI registry which supports via API deletion; Clean up for OCI registry repo must be added before this test.")
def test_spack_create_cache_concretization(tmp_path):
    install_dir = tmp_path
    spack_operation, _ = setup(install_dir)
    assert isinstance(spack_operation, SpackOperationCreateCache)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env()
    assert len(spack_operation.cache_dependency.list_tags()) > 0


@pytest.mark.skip(
    reason="Skipping until an OCI registry which supports via API deletion; Clean up for OCI registry repo must be added before this test.")
def test_spack_create_cache_installation(tmp_path):
    install_dir = tmp_path
    spack_operation, env_path = setup(install_dir)
    assert isinstance(spack_operation, SpackOperationCreateCache)
    spack_operation.install_spack(bashrc_path=str(install_dir / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env()
    assert len(spack_operation.cache_dependency.list_tags()) > 0
    spack_operation.install_packages()
    assert len(spack_operation.build_cache.list_tags()) > 0
    assert spack_operation.check_installed_spack_packages(env_path) == True
