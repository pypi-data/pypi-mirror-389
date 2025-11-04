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
import pathlib
import ruamel.yaml as yaml
import spack


parser = argparse.ArgumentParser(
        prog='specfile_dag_hash.py',
        description='Extracting DAG hashes from a given specfile',
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

    for spec in maybe_to_be_fetched:
        if (not args.include_installed) and spec.installed:
            continue
        to_be_fetched.add(spec.dag_hash())

for dag_hash in to_be_fetched:
    print(dag_hash)
