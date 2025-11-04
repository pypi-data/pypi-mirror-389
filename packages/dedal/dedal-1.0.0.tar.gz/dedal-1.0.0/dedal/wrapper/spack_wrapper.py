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

import functools

from dedal.error_handling.exceptions import NoSpackEnvironmentException


def check_spack_env(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if self.spack_env_exists():
            return method(self, *args, **kwargs)
        else:
            self.logger.debug('No spack environment defined')
            raise NoSpackEnvironmentException('No spack environment defined')

    return wrapper
