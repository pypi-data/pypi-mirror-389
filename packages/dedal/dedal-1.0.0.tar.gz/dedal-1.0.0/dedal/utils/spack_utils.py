# Dedal library - Wrapper over Spack for building multiple target
# environments: ESD, Virtual Boxes, HPC compatible kernels, etc.
import os

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

import yaml
import re


def extract_spack_packages(spack_yaml_path: str):
    """
    Extracts only the package names from a spack.yaml file, ignoring versions, variants, compilers, and dependencies.
    Args:
        spack_yaml_path (str): Path to the spack.yaml file.
    Returns:
        List[str]: Clean list of package names.
    """
    with open(spack_yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    specs = data.get('spack', {}).get('specs', [])
    package_names = []
    for spec in specs:
        if isinstance(spec, str):
            # Match the first word-like token before any of: @ + % ^ whitespace
            match = re.match(r'^([\w-]+)', spec.strip())
            if match:
                package_names.append(match.group(1))

    return package_names


def find_first_upstream_prefix(upstream_instance):
    """
    Search for directories named '.spack-db' within the spack opt directory
    under upstream_instance, and return a list of their parent directories.
    """
    base_path = os.path.join(upstream_instance, "spack", "opt", "spack")
    for upstream_prefix, dirs, _ in os.walk(base_path):
        if ".spack-db" in dirs:
            return upstream_prefix
    return None
