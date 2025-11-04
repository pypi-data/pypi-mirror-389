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

from dedal.configuration.SpackConfig import SpackConfig
from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.spack_factory.SpackOperationCreator import SpackOperationCreator
from dedal.spack_factory.SpackOperationUseCache import SpackOperationUseCache
from dedal.tests.integration_tests.helper import get_test_path
from dedal.utils.utils import file_exists_and_not_empty, count_files_in_folder
from dedal.utils.variables import test_spack_env_git, ebrains_spack_builds_git


def setup(path):
    install_dir = path
    env_name = 'test-spack-env'
    env_path = install_dir / env_name
    env = SpackDescriptor(env_name, install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    concretization_dir = install_dir / 'concretize'
    buildcache_dir = install_dir / 'buildcache'
    spack_config = SpackConfig(env, install_dir=install_dir, concretization_dir=concretization_dir,
                               buildcache_dir=buildcache_dir)
    spack_config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config, use_cache=True)
    return spack_operation, concretization_dir, buildcache_dir, env_path


def test_spack_from_cache_setup():
    install_dir = get_test_path()
    spack_operation, concretization_dir, buildcache_dir, _ = setup(install_dir)
    assert isinstance(spack_operation, SpackOperationUseCache)
    spack_operation.install_spack(bashrc_path=str(install_dir / Path('.bashrc')))
    spack_operation.setup_spack_env()
    num_tags = len(spack_operation.build_cache.list_tags())
    concretization_download_file_path = concretization_dir / 'spack.lock'
    assert file_exists_and_not_empty(concretization_download_file_path) == True
    assert count_files_in_folder(buildcache_dir) == num_tags + 2
    assert 'local_cache' in spack_operation.mirror_list()


def test_spack_from_cache_concretize():
    install_dir = get_test_path()
    spack_operation, concretization_dir, buildcache_dir, _ = setup(install_dir)
    assert isinstance(spack_operation, SpackOperationUseCache)
    spack_operation.install_spack(bashrc_path=str(install_dir / Path('.bashrc')))
    spack_operation.setup_spack_env()
    num_tags = len(spack_operation.build_cache.list_tags())
    concretization_download_file_path = concretization_dir / 'spack.lock'
    assert file_exists_and_not_empty(concretization_download_file_path) == True
    assert count_files_in_folder(buildcache_dir) == num_tags + 2
    assert 'local_cache' in spack_operation.mirror_list()
    assert spack_operation.concretize_spack_env() == False
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


def test_spack_from_cache_install_1():
    install_dir = get_test_path()
    spack_operation, concretization_dir, buildcache_dir, env_path = setup(install_dir)
    assert isinstance(spack_operation, SpackOperationUseCache)
    spack_operation.install_spack(bashrc_path=str(install_dir / Path('.bashrc')))
    spack_operation.setup_spack_env()
    num_tags = len(spack_operation.build_cache.list_tags())
    concretization_download_file_path = concretization_dir / 'spack.lock'
    assert file_exists_and_not_empty(concretization_download_file_path) == True
    assert count_files_in_folder(buildcache_dir) == num_tags + 2
    assert 'local_cache' in spack_operation.mirror_list()
    assert spack_operation.concretize_spack_env() == False
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True
    install_result = spack_operation.install_packages(jobs=2, debug=False)
    assert install_result.returncode == 0
    assert spack_operation.check_installed_spack_packages(env_path) == True


def test_spack_from_cache_install_2():
    install_dir = get_test_path()
    spack_operation, concretization_dir, buildcache_dir, env_path = setup(install_dir)
    assert isinstance(spack_operation, SpackOperationUseCache)
    spack_operation.install_spack(bashrc_path=str(install_dir / Path('.bashrc')))
    spack_operation.setup_spack_env()
    num_tags = len(spack_operation.build_cache.list_tags())
    concretization_download_file_path = concretization_dir / 'spack.lock'
    assert file_exists_and_not_empty(concretization_download_file_path) == True
    assert count_files_in_folder(buildcache_dir) == num_tags + 2
    assert 'local_cache' in spack_operation.mirror_list()
    assert spack_operation.concretize_spack_env() == False
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True
    install_result = spack_operation.install_packages(jobs=2, debug=False, test='root')
    assert install_result.returncode == 0
    assert spack_operation.check_installed_spack_packages(env_path) == True
