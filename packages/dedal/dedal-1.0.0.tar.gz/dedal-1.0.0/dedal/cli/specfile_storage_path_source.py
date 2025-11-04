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

import argparse
from collections.abc import Iterable
import llnl.util.filesystem as fsys
import os
import pathlib
import ruamel.yaml as yaml
import spack
import sys

parser = argparse.ArgumentParser(
        prog='specfile_storage_path_source.py',
        description='Extracting storage paths to the source cache from a given specfile',
        epilog='...')

parser.add_argument(
    "path_specfile", type=pathlib.Path,
    help="Location of the specfile to parse")

parser.add_argument(
    "--include-installed",
    action='store_true', default=False,
    help="Include already installed specs.")

args = parser.parse_args()

with open(args.path_specfile, "r") as fd:
    file_content = fd.read()
    data = list(yaml.safe_load_all(file_content))

to_be_fetched = set()
for rspec in data:
    s = spack.spec.Spec.from_dict(rspec)
    if not isinstance(s, Iterable):
        s = [s]

    maybe_to_be_fetched = spack.traverse.traverse_nodes(s, key=spack.traverse.by_dag_hash)
    
    for ss in maybe_to_be_fetched:
        if (not args.include_installed) and ss.installed:
            continue

        pkg = ss.package

        # Some packages are not cachable (e.g. branch-name-only versions, or BundlePackages)
        if not pkg.fetcher.cachable:
            continue

        # TODO: pkg.fetcher.mirror_id() might be almost sufficient…)

        format_string = "{name}-{version}"
        pretty_name = pkg.spec.format_path(format_string)
        cosmetic_path = os.path.join(pkg.name, pretty_name)
        to_be_fetched.add(str(spack.mirror.mirror_archive_paths(pkg.fetcher, cosmetic_path).storage_path))
        for resource in pkg._get_needed_resources():
            pretty_resource_name = fsys.polite_filename(f"{resource.name}-{pkg.version}")
            to_be_fetched.add(str(spack.mirror.mirror_archive_paths(resource.fetcher, pretty_resource_name).storage_path))
        for patch in ss.patches:
            if isinstance(patch, spack.patch.UrlPatch):
                to_be_fetched.add(str(spack.mirror.mirror_archive_paths(patch.stage.fetcher, patch.stage.name).storage_path))

for elem in to_be_fetched:
    print(elem)
