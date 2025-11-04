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
import sys
from pathlib import Path
from typing import List

from dedal.build_cache.BuildCacheManagerOciDefault import BuildCacheManagerOciDefault
from dedal.logger.logger_builder import get_logger

default_remote_cache = (("HARBOR_HOST" in os.environ) and ("HARBOR_PROJECT" in os.environ)) and (
    "{}/{}/source_cache".format(os.environ["HARBOR_HOST"], os.environ["HARBOR_PROJECT"])) or ""
default_remote_cache_type = 'oci'
default_remote_cache_username = "HARBOR_USERNAME" in os.environ and Path(os.environ["HARBOR_USERNAME"]) or ""
default_remote_cache_password = "HARBOR_PASSWORD" in os.environ and Path(os.environ["HARBOR_PASSWORD"]) or None
default_local_cache = "YASHCHIKI_CACHE_SOURCE" in os.environ and Path(
    os.environ["YASHCHIKI_CACHE_SOURCE"]) or os.path.expanduser("~/.dedal/cache/")


# migration of /cli/update_cached_sources.py
class CachedSourceUploader:
    def __init__(
            self,
            path_missing: Path,
            remote_cache: str = default_remote_cache,
            remote_cache_type: str = default_remote_cache_type,
            remote_cache_username: str = default_remote_cache_username,
            remote_cache_password: str = default_remote_cache_password,
            local_cache: str = default_local_cache
    ):
        self.path_missing = path_missing
        self.remote_cache = remote_cache
        self.remote_cache_type = remote_cache_type
        self.remote_cache_username = remote_cache_username
        self.remote_cache_password = remote_cache_password
        self.local_cache = Path(local_cache).resolve()
        self.logger = get_logger(__name__)

        self.oci = None
        if remote_cache_type == "oci":
            parts = self.remote_cache.split("/")
            if len(parts) < 3:
                raise ValueError("Remote cache must be in the format <host>/<project>/<version>")
            registry_host = parts[0]
            registry_project = parts[1]
            cache_version = parts[2] if len(parts) > 2 else 'source_cache'
            self.oci = BuildCacheManagerOciDefault(
                registry_host=registry_host,
                registry_project=registry_project,
                registry_username=self.remote_cache_username,
                registry_password=self.remote_cache_password,
                cache_version=cache_version,
            )
            if self.oci is None:
                raise RuntimeError("Failed to initialize BuildCacheManagerOci")

    def upload_missing_sources(self):
        if not self.path_missing.exists():
            self.logger.info(f"File w/ missing cached source information is not available: {self.path_missing}")
            sys.exit(0)

        with open(self.path_missing, "r") as fd:
            missing_file_paths: List[str] = fd.readlines()

        for path in missing_file_paths:
            stripped_path = path.strip()
            full_path = self.local_cache / stripped_path
            if not full_path.exists():
                self.logger.info(f"Missing file not found in local cache: {full_path}")
                continue

            tag = os.path.basename(stripped_path)
            rel_path = os.path.dirname(stripped_path)
            try:
                self.oci.client.push(
                    files=[str(full_path)],
                    target=f"{self.remote_cache}:{tag}",
                    manifest_annotations={"path": rel_path},
                    disable_path_validation=True
                )
                self.logger.info(f"Successfully uploaded '{stripped_path}' to '{self.remote_cache}:{tag}'")
            except Exception as e:
                self.logger.info(f"Uploading of '{stripped_path}' to '{self.remote_cache}:{tag}' failed. Reason: {e}")
