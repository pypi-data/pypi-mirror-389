# spack-python script that merges two environment configuration files (spack.yaml) into one
# Usage: spack-python /path/to/first/spack.yaml /path/to/second/spack.yaml
# (note: if the second file does not exist, the output is the first file

import sys, os
from spack.config import merge_yaml, read_config_file, syaml

if not os.path.exists(sys.argv[2]):
    merged = syaml.dump(read_config_file(sys.argv[1]))
else:
    merged = syaml.dump(merge_yaml(read_config_file(sys.argv[1]), read_config_file(sys.argv[2])))

print(merged)

