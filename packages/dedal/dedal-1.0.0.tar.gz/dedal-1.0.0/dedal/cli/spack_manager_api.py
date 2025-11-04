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
import click
import jsonpickle

from dedal.bll.SpackManager import SpackManager
from dedal.bll.cli_utils import save_config, load_config
from dedal.configuration.GpgConfig import GpgConfig
from dedal.configuration.SpackConfig import SpackConfig
from dedal.enum.SpackViewEnum import SpackViewEnum
from dedal.model.SpackDescriptor import SpackDescriptor
from dedal.utils.utils import resolve_path

SESSION_CONFIG_PATH = os.path.expanduser('/tmp/dedal/dedal_session.json')
os.makedirs(os.path.dirname(SESSION_CONFIG_PATH), exist_ok=True)


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    config = load_config(SESSION_CONFIG_PATH)
    if ctx.invoked_subcommand not in ['set-config', 'install-spack'] and not config:
        click.echo('No configuration set. Use `set-config` first.')
        ctx.exit(1)
    if config:
        config['env_path'] = resolve_path(config['env_path'])
        env = SpackDescriptor(config['env_name'], config['env_path'], config['env_git_path'])
        gpg = GpgConfig(config['gpg_name'], config['gpg_mail']) if config['gpg_name'] and config['gpg_mail'] else None
        spack_config = SpackConfig(env=env, repos=None, install_dir=config['install_dir'],
                                   upstream_instance=config['upstream_instance'],
                                   concretization_dir=config['concretization_dir'],
                                   buildcache_dir=config['buildcache_dir'],
                                   system_name=config['system_name'], gpg=gpg,
                                   use_spack_global=config['use_spack_global'],
                                   view=config['view'],
                                   override_cache=config['override_cache'])
        ctx.obj = SpackManager(spack_config, use_cache=config['use_cache'])


@cli.command()
@click.option('--use_cache', is_flag=True, default=False, help='Enables cashing')
@click.option('--use_spack_global', is_flag=True, default=False, help='Uses spack installed globally on the os')
@click.option('--env_name', type=str, default=None, help='Environment name')
@click.option('--env_path', type=str, default=None, help='Environment path to download locally')
@click.option('--env_git_path', type=str, default=None, help='Git path to download the environment')
@click.option('--install_dir', type=str,
              help='Install directory for installing spack; spack environments and repositories are stored here')
@click.option('--upstream_instance', type=str, default=None, help='Upstream instance for spack environment')
@click.option('--system_name', type=str, default=None, help='System name; it is used inside the spack environment')
@click.option('--concretization_dir', type=str, default=None,
              help='Directory where the concretization caching (spack.lock) will be downloaded')
@click.option('--buildcache_dir', type=str, default=None,
              help='Directory where the binary caching is downloaded for the spack packages')
@click.option('--gpg_name', type=str, default=None, help='Gpg name')
@click.option('--gpg_mail', type=str, default=None, help='Gpg mail contact address')
@click.option('--cache_version_concretize', type=str, default='v1', help='Cache version for concretizaion data')
@click.option('--cache_version_build', type=str, default='v1', help='Cache version for binary caches data')
@click.option('--view', type=SpackViewEnum, default=SpackViewEnum.VIEW, help='Spack environment view')
@click.option('--override_cache', is_flag=True, default=True, help='Flag for overriding existing cache')
def set_config(use_cache, env_name, env_path, env_git_path, install_dir, upstream_instance, system_name,
               concretization_dir,
               buildcache_dir, gpg_name, gpg_mail, use_spack_global, cache_version_concretize, cache_version_build,
               view, override_cache):
    """Sets configuration parameters for the session."""
    spack_config_data = {
        'use_cache': use_cache,
        'env_name': env_name,
        'env_path': env_path,
        'env_git_path': env_git_path,
        'install_dir': install_dir,
        'upstream_instance': upstream_instance,
        'system_name': system_name,
        'concretization_dir': Path(concretization_dir) if concretization_dir else None,
        'buildcache_dir': Path(buildcache_dir) if buildcache_dir else None,
        'gpg_name': gpg_name,
        'gpg_mail': gpg_mail,
        'use_spack_global': use_spack_global,
        'repos': [],
        'cache_version_concretize': cache_version_concretize,
        'cache_version_build': cache_version_build,
        'view': view,
        'override_cache': override_cache,
    }
    save_config(spack_config_data, SESSION_CONFIG_PATH)
    click.echo('Configuration saved.')


@click.command()
def show_config():
    """Show the current configuration."""
    config = load_config(SESSION_CONFIG_PATH)
    if config:
        click.echo(jsonpickle.encode(config, indent=2))
    else:
        click.echo('No configuration set. Use `set-config` first.')


@cli.command()
@click.option('--spack_version', type=str, default='0.23.0',
              help='Specifies the Spack version to be installed (default: v0.23.0).')
@click.option('--bashrc_path', type=str, default="~/.bashrc", help='Defines the path to .bashrc.')
@click.pass_context
def install_spack(ctx: click.Context, spack_version: str, bashrc_path: str):
    """Install spack in the install_dir folder"""
    bashrc_path = os.path.expanduser(bashrc_path)
    if ctx.obj is None:
        SpackManager().install_spack(spack_version, bashrc_path)
    else:
        ctx.obj.install_spack(spack_version, bashrc_path)


@cli.command()
@click.option('--repo_name', type=str, required=True, default=None, help='Repository name')
@click.option('--path', type=str, required=True, default=None, help='Repository path to download locally')
@click.option('--git_path', type=str, required=True, default=None, help='Git path to download the repository')
def add_spack_repo(repo_name: str, path: str, git_path: str = None):
    """Adds a spack repository to the spack environments. The setup command must be rerun."""
    path = resolve_path(path)
    repo = SpackDescriptor(repo_name, path, git_path)
    config = load_config(SESSION_CONFIG_PATH)
    config['repos'].append(repo)
    save_config(config, SESSION_CONFIG_PATH)
    click.echo('dedal setup_spack_env must be reran after each repo is added for the environment.')


@cli.command()
@click.pass_context
def setup_spack_env(ctx: click.Context):
    """Setups a spack environment according to the given configuration."""
    ctx.obj.setup_spack_env()


@cli.command()
@click.pass_context
def concretize(ctx: click.Context):
    """Spack concretization step."""
    ctx.obj.concretize_spack_env()


@cli.command()
@click.option('--jobs', type=int, default=2, help='Number of parallel jobs for spack installation')
@click.pass_context
def install_packages(ctx: click.Context, jobs):
    """Installs spack packages present in the spack environment defined in configuration."""
    ctx.obj.install_packages(jobs=jobs)


@click.command()
def clear_config():
    """Clears stored configuration."""
    if os.path.exists(SESSION_CONFIG_PATH):
        os.remove(SESSION_CONFIG_PATH)
        click.echo('Configuration cleared!')
    else:
        click.echo('No configuration to clear.')


cli.add_command(show_config)
cli.add_command(clear_config)

if __name__ == '__main__':
    cli()
