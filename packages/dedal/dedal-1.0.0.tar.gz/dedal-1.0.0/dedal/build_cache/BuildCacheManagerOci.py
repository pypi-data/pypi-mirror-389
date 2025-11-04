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

import glob
import os
from os.path import join
from pathlib import Path
from dedal.build_cache.BuildCacheManagerInterface import BuildCacheManagerInterface
from dedal.build_cache.BuildCacheManagerOciDefault import BuildCacheManagerOciDefault


class BuildCacheManagerOci(BuildCacheManagerOciDefault, BuildCacheManagerInterface):
    """
        This class aims to manage the push/pull/delete of build cache files
    """

    def upload(self, upload_dir: Path, override_cache=True):
        """
            This method pushed all the files from the build cache folder into the OCI Registry
            Args:
                upload_dir (Path): directory with the local binary caches
                override_cache (bool): Updates the cache from the OCI Registry with the same tag
        """
        build_cache_path = upload_dir.resolve()
        # build cache folder must exist before pushing all the artifacts
        if not build_cache_path.exists():
            self._logger.error(f"Path {build_cache_path} not found.")

        tags = self.list_tags()

        for sub_path in build_cache_path.rglob("*"):
            if sub_path.is_file():
                tag = str(sub_path.name)
                rel_path = str(sub_path.relative_to(build_cache_path)).replace(tag, "")
                target = f"{self._registry_host}/{self._registry_project}/{self.cache_version}:{tag}"
                upload_file = True
                if override_cache is False and tag in tags:
                    upload_file = False
                if upload_file:
                    try:
                        self._logger.info(f"Pushing file '{sub_path}' to ORAS target '{target}' ...")
                        self.client.push(
                            files=[str(sub_path)],
                            target=target,
                            # save in manifest the relative path for reconstruction
                            manifest_annotations={"path": rel_path},
                            disable_path_validation=True,
                        )
                        self._logger.info(f"Successfully pushed {tag}")
                    except Exception as e:
                        self._logger.error(
                            f"An error occurred while pushing: {e}")
                else:
                    self._logger.info(f"File '{sub_path}' already uploaded ...")

    def download(self, download_dir: Path):
        """
            This method pulls all the files from the OCI Registry into the build cache folder
        """
        build_cache_path = download_dir.resolve()
        # create the buildcache dir if it does not exist
        os.makedirs(build_cache_path, exist_ok=True)
        tags = self.list_tags()
        if tags is not None:
            for tag in tags:
                ref = f"{self._registry_host}/{self._registry_project}/{self.cache_version}:{tag}"
                # reconstruct the relative path of each artifact by getting it from the manifest
                cache_path = \
                    self.client.get_manifest(
                        f'{self._registry_host}/{self._registry_project}/{self.cache_version}:{tag}')[
                        'annotations'][
                        'path']
                try:
                    self.client.pull(
                        ref,
                        outdir=str(build_cache_path / cache_path),
                        overwrite=True
                    )
                    self._logger.info(f"Successfully pulled artifact {tag}.")
                except Exception as e:
                    self._logger.error(
                        f"Failed to pull artifact {tag} : {e}")

    def delete(self):
        """
            Deletes all artifacts from an OCI Registry based on their tags.
            This method removes artifacts identified by their tags in the specified OCI Registry.
            It requires appropriate permissions to delete artifacts from the registry.
            If the registry or user does not have the necessary delete permissions, the operation might fail.
        """
        tags = self.list_tags()
        if tags is not None:
            try:
                self.client.delete_tags(self._oci_registry_path, tags)
                self._logger.info("Successfully deleted all artifacts form OCI registry.")
            except RuntimeError as e:
                self._logger.error(
                    f"Failed to delete artifacts: {e}")

    def __log_warning_if_needed(self, warn_message: str, items: list[str]) -> None:
        """Logs a warning message if the number of items is greater than 1. (Private function)
           This method logs a warning message using the provided message and items if the list of items has more than one element.

        Args:
            warn_message (str): The warning message to log.
            items (list[str]): The list of items to include in the log message.
        """
        if len(items) > 1:
            self._logger.warning(warn_message, items, items[0])

    def get_public_key_from_cache(self, build_cache_dir: str | None) -> str | None:
        """Retrieves the public key from the build cache.
            This method searches for the public key within the specified build cache directory.
        Args:
            build_cache_dir (str | None): The path to the build cache directory.
        Returns:
            str | None: The path to the public key file if found, otherwise None.
        """

        if not build_cache_dir or not os.path.exists(build_cache_dir):
            self._logger.warning("Build cache directory does not exist!")
            return None
        pgp_folders = glob.glob(f"{build_cache_dir}/**/_pgp", recursive=True)
        if not pgp_folders:
            self._logger.warning("No _pgp folder found in the build cache!")
            return None
        self.__log_warning_if_needed(
            "More than one PGP folders found in the build cache: %s, using the first one in the list: %s", pgp_folders)
        pgp_folder = pgp_folders[0]
        key_files = glob.glob(join(pgp_folder, "**"))
        if not key_files:
            self._logger.warning("No PGP key files found in the build cache!")
            return None
        self.__log_warning_if_needed(
            "More than one PGP key files found in the build cache: %s, using the first one in the list: %s", key_files)
        return key_files[0]
