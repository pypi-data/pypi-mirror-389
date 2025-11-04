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
from typing import List
from dedal.build_cache.BuildCacheManagerOciDefault import BuildCacheManagerOciDefault
from dedal.build_cache.SpecfileSourceStoragePathExtractor import SpecfileSourceStoragePathExtractor
from dedal.logger.logger_builder import get_logger

default_remote_cache = ("HARBOR_HOST" in os.environ and "HARBOR_PROJECT" in os.environ) and (
    "{}/{}/source_cache".format(os.environ["HARBOR_HOST"], os.environ["HARBOR_PROJECT"])) or ""
default_remote_cache_username = "HARBOR_USERNAME" in os.environ and Path(os.environ["HARBOR_USERNAME"]) or ''
default_remote_cache_password = "HARBOR_PASSWORD" in os.environ and Path(os.environ["HARBOR_PASSWORD"]) or None
default_local_cache = "YASHCHIKI_CACHE_SOURCE" in os.environ and Path(
    os.environ["YASHCHIKI_CACHE_SOURCE"]) or os.path.expanduser("~/.dedal/cache/")


# migration of /cli/fetch_cached_sources.py
class CachedSourceFetcher:
    def __init__(self, path_missing: Path, specfiles: List[str], remote_cache: str = default_remote_cache,
                 remote_cache_type: str = 'oci',
                 remote_cache_username: str = default_remote_cache_username,
                 remote_cache_password: str = default_remote_cache_password,
                 local_cache: str = default_local_cache,
                 dedal_home: str = '',
                 include_installed: bool = False):
        self.logger = get_logger(__name__)
        self.path_missing = path_missing
        self.specfiles = specfiles
        self.remote_cache = remote_cache
        self.local_cache = Path(local_cache)
        self.dedal_home = dedal_home
        self.include_installed = include_installed
        self.oci = None
        if remote_cache_type == "oci":
            registry_host, registry_project_version = remote_cache.split('/', 1)
            registry_project, cache_version = registry_project_version.rsplit('/', 1)
            self.oci = BuildCacheManagerOciDefault(
                registry_host=registry_host,
                registry_project=registry_project,
                registry_username=remote_cache_username,
                registry_password=remote_cache_password,
                cache_version=cache_version
            )

    def fetch(self):
        if not self.local_cache.exists():
            self.logger.info("Creating local cache directory")
            self.local_cache.mkdir(parents=True, exist_ok=False)

        missing_paths = []
        available_paths = []
        cached_paths = self.oci.list_tags() if self.oci else []

        for specfile in self.specfiles:
            with open(specfile, "r") as fd:
                try:
                    extractor = SpecfileSourceStoragePathExtractor(path_specfile=specfile,
                                                                   include_installed=self.include_installed)
                    fetch_paths = extractor.extract_paths()
                except Exception as e:
                    self.logger.info(f"Error extracting paths from {specfile}: {e}")
                    continue

                for fetch_path in fetch_paths:
                    basename = os.path.basename(fetch_path)
                    if basename in cached_paths:
                        try:
                            self.oci.client.pull(
                                ref=f"{self.remote_cache}:{basename}",
                                outdir=str(self.local_cache),
                                overwrite=True
                            )
                            available_paths.append(fetch_path)
                        except Exception:
                            self.logger.info(f"Pulling of \"{basename}\" from \"{self.remote_cache}\" failed.")
                            missing_paths.append(fetch_path)
                    else:
                        missing_paths.append(fetch_path)

        self.logger.info(len(missing_paths), "missing files in remote source cache.")
        self.logger.info(len(available_paths), "available files in remote source cache.")

        if missing_paths:
            with open(self.path_missing, "w") as fd:
                fd.write("\n".join(missing_paths))
