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
import pathlib
import subprocess
from typing import List

from dedal.build_cache.BuildCacheManagerOciDefault import BuildCacheManagerOciDefault
from dedal.build_cache.SpecfileBuildStoragePathExtractor import SpecfileBuildStoragePathExtractor
from dedal.logger.logger_builder import get_logger

default_local_cache = "YASHCHIKI_CACHE_BUILD" in os.environ and pathlib.Path(
    os.environ["YASHCHIKI_CACHE_BUILD"]) or os.path.expanduser("~/.dedal/cache/")
default_remote_cache = ("HARBOR_HOST" in os.environ) and ("HARBOR_PROJECT" in os.environ) and (
    "{}/{}/build_cache".format(os.environ["HARBOR_HOST"], os.environ["HARBOR_PROJECT"])) or ""
default_remote_cache_username = "HARBOR_USERNAME" in os.environ and pathlib.Path(os.environ["HARBOR_USERNAME"]) or ""
default_remote_cache_password = "HARBOR_PASSWORD" in os.environ and pathlib.Path(os.environ["HARBOR_PASSWORD"]) or None


# migration of /cli/fetch_cached_buildresults.py
class CachedBuildResultsFetcher:
    def __init__(self, path_missing: pathlib.Path, specfiles: List[str], dedal_home: str,
                 remote_cache: str = default_remote_cache,
                 remote_cache_type: str = "oci", remote_cache_username: str = default_remote_cache_username,
                 remote_cache_password: str = default_remote_cache_password,
                 local_cache: str = default_local_cache, include_installed: bool = False):
        self.path_missing = pathlib.Path(path_missing)
        self.specfiles = specfiles
        self.dedal_home = dedal_home
        self.remote_cache = remote_cache
        self.remote_cache_type = remote_cache_type
        self.remote_cache_username = remote_cache_username
        self.remote_cache_password = remote_cache_password
        self.local_cache = pathlib.Path(local_cache)
        self.include_installed = include_installed
        self.logger = get_logger(__name__)

        if self.local_cache.exists():
            self.logger.info("Creating local build cache directory")
            self.local_cache.mkdir(parents=True, exist_ok=False)

        host, project, _ = self.remote_cache.split("/", 2)
        self.oci = BuildCacheManagerOciDefault(
            registry_host=host,
            registry_project=project,
            registry_username=self.remote_cache_username,
            registry_password=self.remote_cache_password,
        )

    def fetch(self):
        cached_paths = self.oci.list_tags()
        missing_packages = []
        available_packages = []

        for specfile in self.specfiles:
            with open(specfile, "r") as fd:
                try:
                    extractor = SpecfileBuildStoragePathExtractor(include_installed=self.include_installed)
                    lines = extractor.extract_paths(pathlib.Path(specfile))
                    packages = {line.split()[0]: line.split()[1:] for line in lines}
                except subprocess.CalledProcessError as e:
                    self.logger.info(f"Computing fetch buildresult paths failed: {str(e)}")
                    continue

                for package_dag_hash, fetch_paths in packages.items():
                    missing_paths = []
                    for fetch_path in fetch_paths:
                        basename = os.path.basename(fetch_path)
                        if basename in cached_paths:
                            try:
                                self.oci.client.pull(
                                    ref=f"{self.remote_cache}:{basename}",
                                    outdir=str(self.local_cache),
                                    overwrite=True
                                )
                            except Exception as e:
                                self.logger.info(f"Pulling of \"{basename}\" from \"{self.remote_cache}\" failed.")
                                missing_paths.append(fetch_path)
                        else:
                            missing_paths.append(fetch_path)

                    if any(p.endswith((".spack", ".spec.json")) for p in missing_paths):
                        missing_packages.append(f"{package_dag_hash} " + " ".join(missing_paths))
                    else:
                        available_packages.append(f"{package_dag_hash} " + " ".join(missing_paths))

        self.logger.info(len(missing_packages), "missing packages in remote buildresults cache.")
        self.logger.info(len(available_packages), "available packages in remote buildresults cache.")

        if missing_packages:
            with open(self.path_missing, "w") as fd:
                fd.write("\n".join(missing_packages))
