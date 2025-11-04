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

from dedal.configuration.SpackConfig import SpackConfig
from dedal.spack_factory.SpackOperation import SpackOperation
from dedal.tests.testing_variables import SPACK_VERSION


def test_spack_install_scratch(tmp_path):
    install_dir = tmp_path
    spack_config = SpackConfig(install_dir=install_dir)
    spack_operation = SpackOperation(spack_config)
    spack_operation.install_spack(spack_version=f'{SPACK_VERSION}')
    installed_spack_version = spack_operation.get_spack_installed_version()
    assert SPACK_VERSION == installed_spack_version

