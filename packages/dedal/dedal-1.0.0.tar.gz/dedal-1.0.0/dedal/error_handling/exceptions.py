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

class SpackException(Exception):

    def __init__(self, message):
        super().__init__(message)
        self.message = str(message)

    def __str__(self):
        return self.message


class BashCommandException(SpackException):
    """
    To be thrown when a bash command has failed
    """


class NoSpackEnvironmentException(BashCommandException):
    """
    To be thrown when an operation on a spack environment is executed without the environment being activated or existent
    """


class SpackConcertizeException(BashCommandException):
    """
    To be thrown when the spack concretization step fails
    """


class SpackInstallPackagesException(BashCommandException):
    """
    To be thrown when the spack fails to install spack packages
    """


class SpackMirrorException(BashCommandException):
    """
    To be thrown when the spack add mirror command fails
    """


class SpackGpgException(BashCommandException):
    """
    To be thrown when the spack fails to create gpg keys
    """


class SpackRepoException(BashCommandException):
    """
    To be thrown when the spack fails to add a repo
    """


class SpackReindexException(BashCommandException):
    """
    To be thrown when the spack reindex step fails
    """


class SpackSpecException(BashCommandException):
    """
    To be thrown when the spack spec for a package fails
    """


class SpackConfigException(BashCommandException):
    """
    To be thrown when the spack config command fails
    """


class SpackFindException(BashCommandException):
    """
    To be thrown when the spack find command fails
    """


class MissingAttributeException(BashCommandException):
    """
    To be thrown when a missing attribute for a class is missing
    """


class SpackFetchException(BashCommandException):
    """
    To be thrown when a fetching fails
    """


class SpackCreateBuildCacheException(BashCommandException):
    """
    To be thrown when a creating a buildcache for a package fails
    """


class SpackMergeEnvsException(BashCommandException):
    """
    To be thrown when merging spack environments fails
    """


class CreateLoadEnvException(BashCommandException):
    """
    To be thrown when creating the load env bash script fails
    """


class SpackAddException(BashCommandException):
    """
    To be thrown when spack add <package> fails
    """


class SpackRemoveException(BashCommandException):
    """
    To be thrown when spack remove <package> fails
    """
