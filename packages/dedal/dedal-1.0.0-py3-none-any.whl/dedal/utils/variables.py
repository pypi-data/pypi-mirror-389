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

SPACK_ENV_ACCESS_TOKEN = os.getenv("SPACK_ENV_ACCESS_TOKEN")
test_spack_env_git = f'https://oauth2:{SPACK_ENV_ACCESS_TOKEN}@gitlab.ebrains.eu/ri/projects-and-initiatives/virtualbraintwin/tools/test-spack-env.git'
test_spack_env_name = 'test-spack-env'
ebrains_spack_builds_git = 'https://gitlab.ebrains.eu/ri/tech-hub/platform/esd/ebrains-spack-builds.git'
