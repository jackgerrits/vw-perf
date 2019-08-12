import os
import time
import subprocess
import util
import shutil

import sys
script_path = os.path.abspath(os.path.dirname(sys.argv[0]))

def get_commit_date(ref):
  repo_info = "./repo_info"
  if not os.path.exists(repo_info):
    print("Cloning {}...".format(ref))
    util.check_result_throw(subprocess.run(("git clone https://github.com/VowpalWabbit/vowpal_wabbit/ {}".format(repo_info)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))

  os.chdir(repo_info)
  result = subprocess.run(("git rev-list --date=iso --format=format:'%ai' --max-count=1 {}".format(ref)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  os.chdir(script_path)
  util.check_result_throw(result)

  date = util.try_decode(result.stdout).splitlines()[1].strip("'")
  # Javascript can't seem to parse the date when there is a space beteen time and timezone, remove it.
  space_index = date.rfind(' ')
  date = date[:space_index] + date[space_index + 1:]

  return date

def get_commits(branch, num = 10):
  repo_info = "./repo_info"
  if not os.path.exists(repo_info):
    print("Cloning {}...".format(branch))
    util.check_result_throw(subprocess.run(("git clone https://github.com/VowpalWabbit/vowpal_wabbit/ {}".format(repo_info)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))

  os.chdir(repo_info)
  result = subprocess.run(("git log {} --pretty=format:\"%h\" --no-patch -{}".format(branch, num)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  os.chdir(script_path)
  util.check_result_throw(result)

  return  [x.strip("'\"") for x in util.try_decode(result.stdout).splitlines()]

def clone_and_build(ref, clone_dir = "./clones/"):
  ref_path = os.path.join(clone_dir, ref)
  if os.path.exists(ref_path):
      print("Skipping {} - already exists".format(ref))
  else:
    print("Cloning {}...".format(ref))
    util.check_result_throw(subprocess.run(("git clone https://github.com/VowpalWabbit/vowpal_wabbit/ {}".format(ref_path)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
    os.chdir(ref_path)
    print("Checking out {}...".format(ref))
    util.check_result_throw(subprocess.run(("git checkout {}".format(ref)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
    print("Building {}...".format(ref))
    util.check_result_throw(subprocess.run(("make".format(ref_path)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
    print("Finished with {}".format(ref))
    os.chdir(script_path)

def run(tags_or_shas):
  for ref in tags_or_shas:
  # for ref in get_commits("master", 50):
    ref_path = os.path.realpath(os.path.join("./clones/", ref))
    try:
      clone_and_build(ref, "./clones/")
    except Exception as e:
      print("Skipping {}, failed with: {}".format(ref, e))
      shutil.rmtree(ref_path)
