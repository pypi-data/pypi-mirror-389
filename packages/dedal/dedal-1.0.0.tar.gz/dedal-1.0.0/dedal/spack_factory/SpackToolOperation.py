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

import glob
import os
from pathlib import Path
from dedal.enum.SpackConfigCommand import SpackConfigCommand
from dedal.error_handling.exceptions import MissingAttributeException
from dedal.spack_factory.SpackEnvOperation import SpackEnvOperation
from dedal.tests.testing_variables import SPACK_VERSION
from dedal.utils.utils import run_command
from dedal.logger.logger_builder import get_logger
from dedal.configuration.SpackConfig import SpackConfig


class SpackToolOperation:
    def __init__(self, spack_config: SpackConfig = SpackConfig(), logger=get_logger(__name__), spack_setup_script=None,
                 spack_dir=Path('./').resolve()):
        self.spack_config = spack_config
        self.logger = logger
        if spack_setup_script:
            self.spack_setup_script = spack_setup_script
        else:
            raise MissingAttributeException(f'Missing attribute for class {__name__}')
        self.spack_dir = spack_dir

    def get_spack_installed_version(self):
        """Returns the spack installed version"""
        spack_version = run_command("bash", "-c", f'{self.spack_setup_script} && spack --version',
                                    capture_output=True, text=True, check=True,
                                    logger=self.logger,
                                    info_msg=f"Getting spack version",
                                    exception_msg=f"Error retrieving Spack version")
        if spack_version:
            return spack_version.stdout.strip().split()[0]
        return None

    def install_spack(self, spack_version=f'{SPACK_VERSION}', spack_repo='https://github.com/spack/spack',
                      bashrc_path=os.path.expanduser("~/.bashrc")):
        """Install spack.
            Args:
                spack_version (str): spack version
                spack_repo (str): Git path to the Spack repository.
                bashrc_path (str): Path to the .bashrc file.
        """
        spack_version = f'v{spack_version}'
        try:
            user = os.getlogin()
        except OSError:
            user = None

        self.logger.info(f"Starting to install Spack into {self.spack_dir} from branch {spack_version}")
        if not self.spack_dir.exists():
            run_command(
                "git", "clone", "--depth", "1",
                "-c", "advice.detachedHead=false",
                "-c", "feature.manyFiles=true",
                "--branch", spack_version, spack_repo, self.spack_dir
                , check=True, logger=self.logger)
            self.logger.debug("Cloned spack")
        else:
            self.logger.debug("Spack already cloned.")

        if bashrc_path:
            # ensure the file exists before opening it
            if not os.path.exists(bashrc_path):
                open(bashrc_path, "w").close()
            # add spack setup commands to .bashrc
            with open(bashrc_path, "a") as bashrc:
                bashrc.write(f'export PATH="{self.spack_dir}/bin:$PATH"\n')
                spack_setup_script = f"source {self.spack_dir / 'share' / 'spack' / 'setup-env.sh'}"
                bashrc.write(f"{spack_setup_script}\n")
            self.logger.info("Added Spack PATH to .bashrc")
        if user:
            run_command("chown", "-R", f"{user}:{user}", self.spack_dir, check=True, logger=self.logger,
                        info_msg='Adding permissions to the logged in user')
        self.logger.info("Spack install completed")
        if self.spack_config.use_spack_global is True and bashrc_path is not None:
            # Restart the bash only of the spack is used globally
            self.logger.info('Restarting bash')
            run_command("bash", "-c", f"source {bashrc_path}", check=True, logger=self.logger, info_msg='Restart bash')
            os.system("exec bash")
        # Configure upstream Spack instance if specified
        if self.spack_config.upstream_instance:
            search_path = os.path.join(self.spack_config.upstream_instance, 'spack', 'opt', 'spack', '**', '.spack-db')
            spack_db_dirs = glob.glob(search_path, recursive=True)
            upstream_prefix = [os.path.dirname(dir) for dir in spack_db_dirs]
            spack_env_operation = SpackEnvOperation(spack_config=self.spack_config,
                                                    spack_setup_script=self.spack_setup_script)
            for prefix in upstream_prefix:
                # todo fix
                spack_env_operation.config(SpackConfigCommand.ADD, f':upstream-spack-instance:install_tree:{prefix}')
            self.logger.info("Added upstream spack instance")
