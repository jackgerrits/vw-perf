import os
from pathlib import Path


def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(Path(os.path.join(root, name)).resolve())
    return result


def extract_ref(path):
    p = Path(path)
    parts = p.parts
    return parts[parts.index("clones") + 1]


def run(bin_name, path):
    for file in find_all(bin_name, path):
        print(file)
