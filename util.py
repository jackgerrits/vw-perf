import os
import errno

class CommandFailed(Exception):
  def __init__(self, args, result_code, stdout, stderr):
    self.args = args
    self.result_code = result_code
    self.stdout = stdout
    self.stderr = stderr
    super().__init__(self,"\"{}\" failed with exit code:{}".format(" ".join(args), result_code))

def check_result(result):
  if(result.returncode != 0):
    print(result.args)
    if result.stderr is not None:
      print(result.stderr.decode("utf-8"))
    if result.stdout is not None:
      print(result.stdout.decode("utf-8"))
    exit(1)

def try_decode(binary_object):
  return binary_object.decode("utf-8") if binary_object is not None else None

def check_result_throw(result):
  if(result.returncode != 0):
    raise CommandFailed(result.args, result.returncode, try_decode(result.stdout), try_decode(result.stderr))

def ensure_dirs_exist(filename):
  if not os.path.exists(os.path.dirname(filename)):
    try:
      os.makedirs(os.path.dirname(filename))
    except OSError as exc: # Guard against race condition
      if exc.errno != errno.EEXIST:
        raise
