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

parser = argparse.ArgumentParser(
        prog='fetch_cached_buildresults.py',
        description='Downloading missing source files to a spack cache.',
        epilog='...')

parser.add_argument(
    "path_missing", type=pathlib.Path,
    help="Location of the output file that will list the packages not yet in the build cache.")

parser.add_argument(
    "specfiles", nargs="+",
    help="Location of the file containing the specs to be available.")

parser.add_argument(
    "--remote-cache", type=str, required=(not (("HARBOR_HOST" in os.environ) and ("HARBOR_PROJECT" in os.environ))),
    default=(("HARBOR_HOST" in os.environ) and ("HARBOR_PROJECT" in os.environ)) and
            ("{}/{}/build_cache".format(os.environ["HARBOR_HOST"], os.environ["HARBOR_PROJECT"])) or "",
    help="Path or URL to remote cache (target).")

parser.add_argument(
    "--remote-cache-type", type=str, choices=["oci"],
    default="oci",
    help="Type of the remote cache.")

parser.add_argument(
    "--remote-cache-username", type=str,
    default="HARBOR_USERNAME" in os.environ and
        pathlib.Path(os.environ["HARBOR_USERNAME"]) or "",
    help="Username for remote cache (if applicable)")

parser.add_argument(
    "--remote-cache-password", type=str,
    default="HARBOR_PASSWORD" in os.environ and
        pathlib.Path(os.environ["HARBOR_PASSWORD"]) or None,
    help="Password for remote cache (if applicable)")

parser.add_argument(
    "--local-cache", type=str,
    default="YASHCHIKI_CACHE_BUILD" in os.environ and
        pathlib.Path(os.environ["YASHCHIKI_CACHE_BUILD"]) or
        os.path.expanduser("~/.yashchiki/cache/"),
    help="Path to local spack cache folder (build results).")

parser.add_argument(
    "--yashchiki-home", type=str, required=True,
    help="Path to yashchiki home for calling helper tools.")

parser.add_argument(
    "--include-installed",
    action='store_true', default=False,
    help="Include already installed specs.")

args = parser.parse_args()

local_cache = pathlib.Path(args.local_cache)
if not os.path.exists(args.local_cache):
    print("Creating local build cache directory")
    local_cache.mkdir(parents=True, exist_ok=False)

missing_packages = []
available_packages = []
cached_paths = []
cmd = ["oras", "repo", "tags"]
if args.remote_cache_username and args.remote_cache_password:
    cmd.extend(["--username", args.remote_cache_username])
    cmd.extend(["--password", args.remote_cache_password])
cmd.append(args.remote_cache)
try:
    tags = subprocess.check_output(cmd)
    tags = tags.decode("utf-8")
    cached_paths = tags.split()
except subprocess.CalledProcessError as e:
    print(f"Listing repo tags of \"{args.remote_cache}\" failed.")

for specfile in args.specfiles:
    with open(specfile, "r") as fd:
        fetch_paths = []
        packages = {}
        try:
            include_installed = " --include-installed" if args.include_installed else ""
            # FIXME: import and call function, but this would need *this to be run in spack-python already
            lines = subprocess.check_output(f"spack-python {args.yashchiki_home}/specfile_storage_path_build.py {specfile}{include_installed}", shell=True)
            lines = lines.decode("utf-8")
            lines = lines.split("\n")
            for line in lines:
                if not line:
                    continue
                elems = line.split()
                packages[elems[0]] = elems[1:]
        except subprocess.CalledProcessError as e:
            print(f"Computing fetch buildresult paths failed:", str(e), e.output)
        for package_dag_hash, fetch_paths in packages.items():
            missing_paths = []
            for fetch_path in fetch_paths:
                basename = os.path.basename(fetch_path)
                if basename in cached_paths:
                    cmd = ["oras", "pull"]
                    if args.remote_cache_username and args.remote_cache_password:
                        cmd.extend(["--username", args.remote_cache_username])
                        cmd.extend(["--password", args.remote_cache_password])
                    cmd.append(args.remote_cache + f":{basename}")
                    try:
                        subprocess.check_output(cmd, stderr=subprocess.STDOUT, cwd=local_cache)
                    except subprocess.CalledProcessError as e:
                        print(f"Pulling of \"{basename}\" from \"{args.remote_cache}\" failed.")
                        missing_paths.append(fetch_path)
                else:
                    missing_paths.append(fetch_path)
            package_missing = False
            for missing_path in missing_paths:
                if missing_path.endswith(".spack") or missing_path.endswith(".spec.json"):
                    package_missing = True
            if package_missing:
                missing_packages.append(f"{package_dag_hash} " + " ".join(missing_paths))
            else:
                available_packages.append(f"{package_dag_hash} " + " ".join(missing_paths))

print(len(missing_packages), "missing packages in remote buildresults cache.")
print(len(available_packages), "available packages in remote buildresults cache.")

if missing_packages:
    with open(args.path_missing, "w") as fd:
        fd.write("\n".join(missing_packages))
