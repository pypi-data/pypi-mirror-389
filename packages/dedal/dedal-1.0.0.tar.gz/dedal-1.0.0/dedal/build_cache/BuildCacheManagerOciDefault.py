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


import builtins
import oras.client
from dedal.logger.logger_builder import get_logger


class BuildCacheManagerOciDefault:
    """
        This class aims to manage the push/pull/delete of build cache files
    """

    def __new__(cls, registry_host, registry_project, registry_username, registry_password, cache_version='cache',
                auth_backend='basic', insecure=False, tls_verify=True):
        instance = super().__new__(cls)
        instance._logger = get_logger(__name__, BuildCacheManagerOciDefault.__name__)
        instance._registry_project = registry_project

        instance._registry_username = registry_username
        instance._registry_password = registry_password

        instance._registry_host = registry_host

        # Override input to disable prompts during login.
        # Define a function that raises an exception when input is called.
        def disabled_input():
            raise Exception("Interactive login disabled: credentials are provided via attributes.")

        # Save the original input function.
        original_input = builtins.input
        # Override input so that any call to input() during login will raise our exception.
        builtins.input = disabled_input
        # Initialize an OrasClient instance.
        # This method utilizes the OCI Registry for container image and artifact management.
        # Refer to the official OCI Registry documentation for detailed information on the available authentication methods.
        # Supported authentication types may include basic authentication (username/password), token-based authentication,
        instance.client = oras.client.OrasClient(hostname=instance._registry_host, auth_backend=auth_backend,
                                                 insecure=insecure, tls_verify=tls_verify)

        try:
            instance.client.login(username=instance._registry_username, password=instance._registry_password)
        except Exception:
            instance._logger.error('Login failed!')
            return None
        finally:
            builtins.input = original_input

        instance.cache_version = cache_version
        instance._oci_registry_path = f'{instance._registry_host}/{instance._registry_project}/{instance.cache_version}'
        return instance

    def list_tags(self):
        """
            This method retrieves all tags from an OCI Registry
        """
        try:
            return self.client.get_tags(self._oci_registry_path)
        except Exception as e:
            self._logger.error(f"Failed to list tags: {e}")
            return []