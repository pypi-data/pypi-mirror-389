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

import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dedal.cli.spack_manager_api import show_config, clear_config, install_spack, add_spack_repo, install_packages, \
    setup_spack_env, concretize, set_config
from dedal.enum.SpackViewEnum import SpackViewEnum
from dedal.model.SpackDescriptor import SpackDescriptor


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mocked_session_path():
    return '/mocked/tmp/session.json'


@pytest.fixture
def mock_spack_manager():
    mock_spack_manager = MagicMock()
    mock_spack_manager.install_spack = MagicMock()
    mock_spack_manager.add_spack_repo = MagicMock()
    mock_spack_manager.setup_spack_env = MagicMock()
    mock_spack_manager.concretize_spack_env = MagicMock()
    mock_spack_manager.install_packages = MagicMock()
    return mock_spack_manager


@pytest.fixture
def mock_load_config():
    with patch('dedal.cli.spack_manager_api.load_config') as mock_load:
        yield mock_load


@pytest.fixture
def mock_save_config():
    with patch('dedal.cli.spack_manager_api.save_config') as mock_save:
        yield mock_save


@pytest.fixture
def mock_clear_config():
    with patch('dedal.cli.spack_manager_api.clear_config') as mock_clear:
        yield mock_clear


def test_show_config_no_config(runner, mock_load_config):
    mock_load_config.return_value = None
    result = runner.invoke(show_config)
    assert 'No configuration set. Use `set-config` first.' in result.output


def test_show_config_with_config(runner, mock_load_config):
    """Test the show_config command when config is present."""
    mock_load_config.return_value = {"key": "value"}
    result = runner.invoke(show_config)
    assert result.exit_code == 0
    assert '"key": "value"' in result.output


def test_clear_config(runner, mock_clear_config):
    """Test the clear_config command."""
    with patch('os.path.exists', return_value=True), patch('os.remove') as mock_remove:
        result = runner.invoke(clear_config)
        assert 'Configuration cleared!' in result.output
        mock_remove.assert_called_once()


def test_install_spack_no_context_1(runner, mock_spack_manager):
    """Test install_spack with no context, using SpackManager."""
    with patch('dedal.cli.spack_manager_api.SpackManager', return_value=mock_spack_manager):
        result = runner.invoke(install_spack, ['--spack_version', '0.24.0'])
    mock_spack_manager.install_spack.assert_called_once_with('0.24.0', os.path.expanduser("~/.bashrc"))
    assert result.exit_code == 0


def test_install_spack_no_context_2(runner, mock_spack_manager):
    """Test install_spack with no context, using SpackManager and the default value for spack_version."""
    with patch('dedal.cli.spack_manager_api.SpackManager', return_value=mock_spack_manager):
        result = runner.invoke(install_spack)
    mock_spack_manager.install_spack.assert_called_once_with('0.23.0', os.path.expanduser("~/.bashrc"))
    assert result.exit_code == 0


def test_install_spack_with_mocked_context_1(runner, mock_spack_manager):
    """Test install_spack with a mocked context, using ctx.obj as SpackManager."""
    result = runner.invoke(install_spack, ['--spack_version', '0.24.0', '--bashrc_path', '/home/.bahsrc'], obj=mock_spack_manager)
    mock_spack_manager.install_spack.assert_called_once_with('0.24.0', '/home/.bahsrc')
    assert result.exit_code == 0


def test_install_spack_with_mocked_context_2(runner, mock_spack_manager):
    """Test install_spack with a mocked context, using ctx.obj as SpackManager and the default value for spack_version."""
    result = runner.invoke(install_spack, obj=mock_spack_manager)
    mock_spack_manager.install_spack.assert_called_once_with('0.23.0', os.path.expanduser("~/.bashrc"))
    assert result.exit_code == 0


def test_setup_spack_env(runner, mock_spack_manager):
    """Test setup_spack_env with a mocked context, using ctx.obj as SpackManager."""
    result = runner.invoke(setup_spack_env, obj=mock_spack_manager)
    mock_spack_manager.setup_spack_env.assert_called_once_with()
    assert result.exit_code == 0


def test_concretize(runner, mock_spack_manager):
    """Test install_spack with a mocked context, using ctx.obj as SpackManager."""
    result = runner.invoke(concretize, obj=mock_spack_manager)
    mock_spack_manager.concretize_spack_env.assert_called_once_with()
    assert result.exit_code == 0


def test_install_packages_1(runner, mock_spack_manager):
    """Test install_packages with a mocked context, using ctx.obj as SpackManager."""
    result = runner.invoke(install_packages, obj=mock_spack_manager)
    mock_spack_manager.install_packages.assert_called_once_with(jobs=2)
    assert result.exit_code == 0


def test_install_packages(runner, mock_spack_manager):
    """Test install_packages with a mocked context, using ctx.obj as SpackManager."""
    result = runner.invoke(install_packages, ['--jobs', 3], obj=mock_spack_manager)
    mock_spack_manager.install_packages.assert_called_once_with(jobs=3)
    assert result.exit_code == 0


@patch('dedal.cli.spack_manager_api.resolve_path')
@patch('dedal.cli.spack_manager_api.SpackDescriptor')
def test_add_spack_repo(mock_spack_descriptor, mock_resolve_path, mock_load_config, mock_save_config,
                        mocked_session_path, runner):
    """Test adding a spack repository with mocks."""
    expected_config = {'repos': [SpackDescriptor(name='test-repo')]}
    repo_name = 'test-repo'
    path = '/path'
    git_path = 'https://example.com/repo.git'
    mock_resolve_path.return_value = '/resolved/path'
    mock_load_config.return_value = expected_config
    mock_repo_instance = MagicMock()
    mock_spack_descriptor.return_value = mock_repo_instance

    with patch('dedal.cli.spack_manager_api.SESSION_CONFIG_PATH', mocked_session_path):
        result = runner.invoke(add_spack_repo, ['--repo_name', repo_name, '--path', path, '--git_path', git_path])

    assert result.exit_code == 0
    assert 'dedal setup_spack_env must be reran after each repo is added' in result.output
    mock_resolve_path.assert_called_once_with(path)
    mock_spack_descriptor.assert_called_once_with(repo_name, '/resolved/path', git_path)
    assert mock_repo_instance in expected_config['repos']
    mock_save_config.assert_called_once_with(expected_config, mocked_session_path)


def test_set_config(runner, mock_save_config, mocked_session_path):
    """Test set_config."""
    with patch('dedal.cli.spack_manager_api.SESSION_CONFIG_PATH', mocked_session_path):
        result = runner.invoke(set_config, ['--env_name', 'test', '--system_name', 'sys'])

    expected_config = {
        'use_cache': False,
        'env_name': 'test',
        'env_path': None,
        'env_git_path': None,
        'install_dir': None,
        'upstream_instance': None,
        'system_name': 'sys',
        'concretization_dir': None,
        'buildcache_dir': None,
        'gpg_name': None,
        'gpg_mail': None,
        'use_spack_global': False,
        'repos': [],
        'cache_version_concretize': 'v1',
        'cache_version_build': 'v1',
        'view': SpackViewEnum.VIEW,
        'override_cache': True,
    }

    mock_save_config.assert_called_once()
    saved_config, saved_path = mock_save_config.call_args[0]
    assert saved_path == mocked_session_path
    assert saved_config == expected_config
    assert result.exit_code == 0
    assert 'Configuration saved.' in result.output
