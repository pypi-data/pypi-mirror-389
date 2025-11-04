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

import jsonpickle
import os


def save_config(spack_config_data, config_path: str):
    """Save config to JSON file."""
    with open(config_path, "w") as data_file:
        data_file.write(jsonpickle.encode(spack_config_data))


def load_config(config_path: str):
    """Load config from JSON file."""
    if os.path.exists(config_path):
        with open(config_path, "r") as data_file:
            data = jsonpickle.decode(data_file.read())
            return data
    return {}


def clear_config(config_path: str):
    """Delete the JSON config file."""
    if os.path.exists(config_path):
        os.remove(config_path)
