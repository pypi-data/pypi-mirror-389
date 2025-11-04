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

from dedal.spack_factory.SpackOperationCreateCache import SpackOperationCreateCache

from dedal.configuration.SpackConfig import SpackConfig
from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.spack_factory.SpackOperation import SpackOperation
from dedal.spack_factory.SpackOperationCreator import SpackOperationCreator
from dedal.spack_factory.SpackOperationUseCache import SpackOperationUseCache
from dedal.tests.testing_variables import ebrains_spack_builds_git, test_spack_env_git


def test_spack_creator_scratch_1(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    spack_config = SpackConfig(env, install_dir=install_dir)
    spack_config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config)
    assert isinstance(spack_operation, SpackOperation)


def test_spack_creator_scratch_2(tmp_path):
    spack_config = None
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config)
    assert isinstance(spack_operation, SpackOperation)


def test_spack_creator_scratch_3():
    spack_config = SpackConfig()
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config)
    assert isinstance(spack_operation, SpackOperation)

def test_spack_creator_scratch_4(tmp_path):
    concretize_oci_host = os.environ.get('CONCRETIZE_OCI_HOST')
    os.environ.pop('CONCRETIZE_OCI_HOST', None)
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    spack_config = SpackConfig(env, install_dir=install_dir, concretization_dir=install_dir, buildcache_dir=install_dir)
    spack_config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config)
    os.environ['CONCRETIZE_OCI_HOST'] = concretize_oci_host
    assert isinstance(spack_operation, SpackOperation)


def test_spack_creator_create_cache(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    spack_config = SpackConfig(env, install_dir=install_dir, concretization_dir=install_dir, buildcache_dir=install_dir)
    spack_config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config)
    assert isinstance(spack_operation, SpackOperationCreateCache)


def test_spack_creator_use_cache(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    spack_config = SpackConfig(env, install_dir=install_dir, concretization_dir=install_dir, buildcache_dir=install_dir)
    spack_config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config, use_cache=True)
    assert isinstance(spack_operation, SpackOperationUseCache)
