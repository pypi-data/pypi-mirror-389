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
import os
import pathlib
import subprocess
import sys

parser = argparse.ArgumentParser(
        prog='update_cached_sources.py',
        description='Uploading previously missing source files to a cache.',
        epilog='...')

parser.add_argument(
    "path_missing", type=pathlib.Path,
    help="Location of the file that lists the hashes and packages not yet in the source cache.")

parser.add_argument(
    "--remote-cache", type=str, required=(not (("HARBOR_HOST" in os.environ) and ("HARBOR_PROJECT" in os.environ))),
    default=(("HARBOR_HOST" in os.environ) and ("HARBOR_PROJECT" in os.environ)) and
            ("{}/{}/source_cache".format(os.environ["HARBOR_HOST"], os.environ["HARBOR_PROJECT"])) or "",
    help="Path or URL to remote cache (target).")

parser.add_argument(
    "--remote-cache-type", type=str, choices=["oci"],
    default="oci",
    help="Type of the remote cache.")

parser.add_argument(
    "--remote-cache-username", type=str, required=(not "HARBOR_USERNAME" in os.environ),
    default="HARBOR_USERNAME" in os.environ and
        pathlib.Path(os.environ["HARBOR_USERNAME"]) or "",
    help="Username for remote cache (if applicable)")

parser.add_argument(
    "--remote-cache-password", type=str, required=(not "HARBOR_PASSWORD" in os.environ),
    default="HARBOR_PASSWORD" in os.environ and
        pathlib.Path(os.environ["HARBOR_PASSWORD"]) or None,
    help="Password for remote cache (if applicable)")

parser.add_argument(
    "--local-cache", type=str,
    default="YASHCHIKI_CACHE_SOURCE" in os.environ and
        pathlib.Path(os.environ["YASHCHIKI_CACHE_SOURCE"]) or
        os.path.expanduser("~/.yashchiki/cache/"),
    help="Path to local spack cache folder (source).")

args = parser.parse_args()

if not os.path.exists(args.path_missing):
    print("File w/ missing cached source information is not available: {}".format(args.path_missing))
    sys.exit(0)

with open(args.path_missing, "r") as fd:
    missing_file_paths = fd.readlines()

    for path in missing_file_paths:
        stripped_path = path.rstrip()
        basename = os.path.basename(stripped_path)
        full_path = pathlib.Path(str(args.local_cache) + "/" + stripped_path)

        cmd = ("oras", "push",
                "--username", args.remote_cache_username,
                "--password", args.remote_cache_password,
                f"--annotation=path={stripped_path}",
                f"{args.remote_cache}:{basename}",
                f"{stripped_path}")
        try:
            subprocess.check_output(cmd, cwd=args.local_cache)
        except subprocess.CalledProcessError as e:
            print(f"Uploading of \"{stripped_path}\" to \"{args.remote_cache}:{basename}\" failed.")
