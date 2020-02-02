import os
import errno
import subprocess
import sys
import hashlib

from typing import Optional

class CommandFailed(Exception):
    def __init__(self, args, result_code, stdout, stderr):
        self.args = args
        self.result_code = result_code
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            self,
            "\"{}\" failed with exit code:{}".format(" ".join(args),
                                                     result_code))


def check_result(result):
    if result.returncode != 0:
        print(result.args)
        if result.stderr is not None:
            print(result.stderr.decode("utf-8"))
        if result.stdout is not None:
            print(result.stdout.decode("utf-8"))
        sys.exit(1)


def try_decode(binary_object: Optional[bytes]) -> Optional[str]:
    return binary_object.decode("utf-8") if binary_object is not None else None


def check_result_throw(result: subprocess.CompletedProcess) -> None:
    if result.returncode != 0:
        raise CommandFailed(result.args, result.returncode,
                            try_decode(result.stdout),
                            try_decode(result.stderr))


def ensure_dirs_exist(filename):
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

def get_file_hash(filename):
    # Read the file in 64kb chunks
    BUF_SIZE = 65536  
    md5 = hashlib.md5()

    with open(filename, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

# TODO: Use this function to ensure testing is always done on release binary.
# The symbols in the binary can be inspected to determine this
def is_release_binary(vw_bin):
    raise NotImplementedError
