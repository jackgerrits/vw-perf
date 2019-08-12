import os
import time
import subprocess
import util
import shutil

import sys
script_path = os.path.abspath(os.path.dirname(sys.argv[0]))

def get_commit_date(commit):
  repo_info = "./repo_info"
  if not os.path.exists(repo_info):
    print("Cloning {}...".format(commit))
    util.check_result_throw(subprocess.run(("git clone https://github.com/VowpalWabbit/vowpal_wabbit/ {}".format(repo_info)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))

  os.chdir(repo_info)
  result = subprocess.run(("git rev-list --date=iso --format=format:'%ai' --max-count=1 {}".format(commit)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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

def clone_and_build(commit, clone_dir = "./clones/"):
  commit_path = os.path.join(clone_dir, commit)
  if os.path.exists(commit_path):
      print("Skipping {} - already exists".format(commit))
  else:
    print("Cloning {}...".format(commit))
    util.check_result_throw(subprocess.run(("git clone https://github.com/VowpalWabbit/vowpal_wabbit/ {}".format(commit_path)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
    os.chdir(commit_path)
    print("Checking out {}...".format(commit))
    util.check_result_throw(subprocess.run(("git checkout {}".format(commit)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
    print("Building {}...".format(commit))
    util.check_result_throw(subprocess.run(("make".format(commit_path)).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
    print("Finished with {}".format(commit))
    os.chdir(script_path)

def run(commits, num):
  if commits is not None:
    commits_to_process = commits
  elif num is not None:
    commits_to_process = get_commits("master", num)
  else:
    print("Error: etiher commits or num must be supplied")
    exit(1)

  for commit in commits_to_process:
    commit_path = os.path.realpath(os.path.join("./clones/", commit))
    try:
      clone_and_build(commit, "./clones/")
    except Exception as e:
      print("Skipping {}, failed with: {}".format(commit, e))
      shutil.rmtree(commit_path)
