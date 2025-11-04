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

from collections.abc import Iterable
import pathlib
import ruamel.yaml as yaml
import spack
import spack.binary_distribution as bindist


# migration of /cli/specfile_storage_path_build.py
class SpecfileBuildStoragePathExtractor:
    def __init__(self, include_installed: bool = False):
        self.include_installed = include_installed

    def extract_paths(self, path_specfile: pathlib.Path):
        with open(path_specfile, "r") as fd:
            file_content = fd.read()
            data = list(yaml.safe_load_all(file_content))

        to_be_fetched = set()

        for rspec in data:
            specs = spack.spec.Spec.from_dict(rspec)
            if not isinstance(specs, Iterable):
                specs = [specs]

            for spec in spack.traverse.traverse_nodes(specs, key=spack.traverse.by_dag_hash):
                if not self.include_installed and spec.installed:
                    continue

                build_cache_paths = [
                    bindist.tarball_path_name(spec, ".spack"),
                    bindist.tarball_name(spec, ".spec.json.sig"),
                    bindist.tarball_name(spec, ".spec.json"),
                    bindist.tarball_name(spec, ".spec.yaml"),
                ]
                to_be_fetched.add(str(spec.dag_hash()) + " " + " ".join(build_cache_paths))

        return list(to_be_fetched)
