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
from pathlib import Path
import sys
from typing import Dict, List
from dedal.build_cache.BuildCacheManagerOciDefault import BuildCacheManagerOciDefault

default_remote_cache = (("HARBOR_HOST" in os.environ) and ("HARBOR_PROJECT" in os.environ)) and (
    "{}/{}/build_cache".format(os.environ["HARBOR_HOST"], os.environ["HARBOR_PROJECT"])) or ""
default_remote_cache_username = "HARBOR_USERNAME" in os.environ and Path(os.environ["HARBOR_USERNAME"]) or ""
default_remote_cache_password = "HARBOR_PASSWORD" in os.environ and Path(os.environ["HARBOR_PASSWORD"]) or None
default_local_cache = "YASHCHIKI_CACHE_BUILD" in os.environ and Path(
    os.environ["YASHCHIKI_CACHE_BUILD"]) or os.path.expanduser("~/.yashchiki/cache/")


# migration of /cli/update_cached_buildresults.py
class CachedBuildResultUploader:
    def __init__(self,
                 path_missing: Path,
                 remote_cache: str=default_remote_cache,
                 remote_cache_username: str=default_remote_cache_username,
                 remote_cache_password: str=default_remote_cache_password,
                 remote_cache_type='oci',
                 local_cache: Path=default_local_cache):

        self.path_missing = path_missing
        self.remote_cache = remote_cache
        self.remote_cache_username = remote_cache_username
        self.remote_cache_password = remote_cache_password
        self.local_cache = local_cache
        self.remote_cache_type=remote_cache_type
        # Extract host and project from the remote_cache URL
        try:
            parts = remote_cache.split('/')
            self.registry_host = parts[0]
            self.registry_project = parts[1]
        except Exception:
            raise ValueError(f"Invalid remote_cache format: {remote_cache}")

        self.oci = BuildCacheManagerOciDefault(
            registry_host=self.registry_host,
            registry_project=self.registry_project,
            registry_username=self.remote_cache_username,
            registry_password=self.remote_cache_password
        )

        if self.oci is None:
            raise RuntimeError("Failed to initialize BuildCacheManagerOci")

    def upload_missing_results(self):
        if not self.path_missing.exists():
            print(f"File with missing cached build information is not available: {self.path_missing}")
            sys.exit(0)

        packages: Dict[str, List[str]] = {}
        with open(self.path_missing, "r") as fd:
            for line in fd:
                elems = line.strip().split()
                if elems:
                    packages[elems[0]] = elems[1:]

        for package_dag_hash, paths in packages.items():
            for path in paths:
                basename = os.path.basename(path)
                full_path = self.local_cache / path

                if ((str(full_path).endswith(".spack") or str(full_path).endswith(
                        ".spec.json")) and not full_path.exists()):
                    print(f"Missing local cache entry for \"{full_path}\"")
                    continue

                if not full_path.exists():
                    # Skip other non-existent files
                    continue

                # Upload file using BuildCacheManagerOci's internal ORAS client
                try:
                    self.oci.client.push(
                        files=[str(full_path)],
                        target=f"{self.remote_cache}:{basename}",
                        manifest_annotations={"path": path},
                        disable_path_validation=True,
                    )
                    print(f"Successfully uploaded {basename} to {self.remote_cache}:{basename}")
                except Exception as e:
                    print(f"Uploading of \"{path}\" to \"{self.remote_cache}:{basename}\" failed: {e}")