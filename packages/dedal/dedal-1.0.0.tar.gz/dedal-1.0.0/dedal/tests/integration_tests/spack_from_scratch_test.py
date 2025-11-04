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
from dedal.configuration.SpackConfig import SpackConfig
from dedal.error_handling.exceptions import BashCommandException, NoSpackEnvironmentException
from dedal.spack_factory.SpackOperationCreator import SpackOperationCreator
from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.tests.testing_variables import test_spack_env_git, ebrains_spack_builds_git
from dedal.utils.utils import file_exists_and_not_empty, git_clone_repo
from dedal.spack_factory.SpackOperation import SpackOperation


def test_spack_repo_exists_1(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('ebrains-spack-builds', install_dir)
    config = SpackConfig(env=env, install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    with pytest.raises(NoSpackEnvironmentException):
        spack_operation.spack_repo_exists(env.name)


def test_spack_repo_exists_2(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('ebrains-spack-builds', install_dir)
    config = SpackConfig(env=env, install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    assert spack_operation.spack_repo_exists(env.name) == False


def test_spack_from_scratch_setup_1(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    config = SpackConfig(env=env, system_name='ebrainslab', install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    assert spack_operation.spack_repo_exists(env.name) == False


def test_spack_reindex(tmp_path):
    install_dir = tmp_path
    config = SpackConfig(install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.reindex()


@pytest.mark.skip(reason="It does not work on bare metal operating systems")
def test_spack_spec(tmp_path):
    install_dir = tmp_path
    config = SpackConfig(install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    assert spack_operation.spec_pacakge('aida') == 'aida@3.2.1'


def test_spack_from_scratch_setup_2(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    repo = env
    config = SpackConfig(env=env, system_name='ebrainslab', install_dir=install_dir)
    config.add_repo(repo)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    assert spack_operation.spack_repo_exists(env.name) == True


def  test_spack_from_scratch_setup_3(tmp_path):
    install_dir = tmp_path
    repo_name = 'ebrains-spack-builds'
    git_clone_repo(repo_name, install_dir / repo_name, ebrains_spack_builds_git)
    env = SpackDescriptor(repo_name, install_dir)
    repo = env
    config = SpackConfig(env=env, system_name='ebrainslab', install_dir=install_dir)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    assert spack_operation.spack_repo_exists(env.name) == True


def test_spack_from_scratch_setup_4(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('new_env1', install_dir)
    repo = env
    config = SpackConfig(env=env, system_name='ebrainslab', install_dir=install_dir)
    config.add_repo(repo)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    with pytest.raises(BashCommandException):
        spack_operation.setup_spack_env()


def test_spack_from_scratch_setup_5(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('new_env2', install_dir)
    config = SpackConfig(env=env, install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    assert spack_operation.spack_env_exists() == True


def test_spack_not_a_valid_repo():
    env = SpackDescriptor('ebrains-spack-builds', Path(), None)
    repo = env
    config = SpackConfig(env=env, system_name='ebrainslab')
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    with pytest.raises(BashCommandException):
        spack_operation.add_spack_repo(repo.path, repo.name)


@pytest.mark.skip(
    reason="Skipping the concretization step because it may freeze when numerous Spack packages are added to the environment.")
def test_spack_from_scratch_concretize_1(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    repo = env
    config = SpackConfig(env=env, system_name='ebrainslab', install_dir=install_dir)
    config.add_repo(repo)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=True)
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


@pytest.mark.skip(
    reason="Skipping the concretization step because it may freeze when numerous Spack packages are added to the environment.")
def test_spack_from_scratch_concretize_2(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    repo = env
    config = SpackConfig(env=env, system_name='ebrainslab', install_dir=install_dir)
    config.add_repo(repo)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=False)
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


def test_spack_from_scratch_concretize_3(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    repo = env
    config = SpackConfig(env=env, system_name='ebrainslab', install_dir=install_dir)
    config.add_repo(repo)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == False


def test_spack_from_scratch_concretize_4(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    config = SpackConfig(env=env, install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=False)
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


def test_spack_from_scratch_concretize_5(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    config = SpackConfig(env=env, install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=True)
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


def test_spack_from_scratch_concretize_6(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    config = SpackConfig(env=env, install_dir=install_dir)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=False)
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


def test_spack_from_scratch_concretize_7(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    config = SpackConfig(env=env, install_dir=install_dir)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=True)
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


def test_spack_from_scratch_concretize_8(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    config = SpackConfig(env=env, install_dir=install_dir)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=True, test='root')
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True


def test_spack_from_scratch_install(tmp_path):
    install_dir = tmp_path
    env_name = 'test-spack-env'
    env_path = install_dir / env_name
    env = SpackDescriptor(env_name, install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    config = SpackConfig(env=env, install_dir=install_dir)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=True)
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True
    install_result = spack_operation.install_packages(jobs=2, signed=False, fresh=True, debug=False)
    assert install_result.returncode == 0
    assert spack_operation.check_installed_spack_packages(env_path) == True


def test_spack_from_scratch_install_2(tmp_path):
    install_dir = tmp_path
    env_name = 'test-spack-env'
    env_path = install_dir / env_name
    env = SpackDescriptor(env_name, install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    config = SpackConfig(env=env, install_dir=install_dir)
    config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    spack_operation.concretize_spack_env(force=True, test='root')
    concretization_file_path = spack_operation.env_path / 'spack.lock'
    assert file_exists_and_not_empty(concretization_file_path) == True
    install_result = spack_operation.install_packages(jobs=2, signed=False, fresh=True, debug=False, test='root')
    assert install_result.returncode == 0
    assert spack_operation.check_installed_spack_packages(env_path) == True


def test_spack_mirror_env(tmp_path):
    install_dir = tmp_path
    env = SpackDescriptor('test-spack-env', install_dir, test_spack_env_git)
    repo = SpackDescriptor('ebrains-spack-builds', install_dir, ebrains_spack_builds_git)
    spack_config = SpackConfig(env, install_dir=install_dir)
    spack_config.add_repo(repo)
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    mirror_dir = tmp_path / Path('./mirror_dir')
    mirror_name = 'mirror_tests'
    spack_operation.add_mirror(mirror_name=mirror_name, mirror_path=mirror_dir)
    assert mirror_name in spack_operation.mirror_list()
    spack_operation.remove_mirror(mirror_name=mirror_name)
    assert mirror_name not in spack_operation.mirror_list()


def test_spack_mirror_global(tmp_path):
    install_dir = tmp_path
    spack_config = SpackConfig(install_dir=install_dir)
    spack_operation = SpackOperationCreator.get_spack_operator(spack_config)
    assert isinstance(spack_operation, SpackOperation)
    spack_operation.install_spack(bashrc_path=str(tmp_path / Path('.bashrc')))
    spack_operation.setup_spack_env()
    mirror_dir = tmp_path / Path('./mirror_dir')
    mirror_name = 'mirror_test'
    spack_operation.add_mirror(mirror_name=mirror_name, mirror_path=mirror_dir)
    assert mirror_name in spack_operation.mirror_list()
    spack_operation.remove_mirror(mirror_name=mirror_name)
    assert mirror_name not in spack_operation.mirror_list()
