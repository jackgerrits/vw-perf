"""This module defines helpers for cloning, building and resolving commits"""

import os
import time
import subprocess
import util
import shutil
import multiprocessing

import sys
from pathlib import Path

from typing import List
script_path = os.path.abspath(os.path.dirname(sys.argv[0]))


def get_commit_info(cache_dir, commit):
    repo_info = os.path.join(cache_dir, "./repo_info")
    update_info_repo(cache_dir)
    os.chdir(repo_info)
    result = subprocess.run(
        (f"git log {commit} --date=iso --pretty=%an;%s;%ad -1").split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    os.chdir(script_path)
    util.check_result_throw(result)

    info = util.try_decode(result.stdout).splitlines()[0].split(";")

    # Javascript can't seem to parse the date when there is a space between time and timezone, remove it.
    space_index = info[2].rfind(' ')
    info[2] = info[2][:space_index] + info[2][space_index + 1:]

    return {"author": info[0], "title": info[1], "date": info[2], "ref": commit}


def update_info_repo(cache_dir, branch: str = "master") -> None:
    repo_info = os.path.join(cache_dir, "./repo_info")
    if not os.path.exists(repo_info):
        print(f"Cloning info repo...")
        util.check_result_throw(
            subprocess.run((
                f"git clone https://github.com/VowpalWabbit/vowpal_wabbit/ {repo_info}"
            ).split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT))
    else:
        os.chdir(repo_info)
        result1 = subprocess.run(f"git checkout {branch}".split(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        result2 = subprocess.run(f"git pull origin {branch}".split(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        os.chdir(script_path)
        util.check_result_throw(result1)
        util.check_result_throw(result2)


def get_commits_raw(directory, range_str: str) -> List[str]:
    os.chdir(directory)
    result = subprocess.run(
        (f"git log --pretty=format:\"%H\" --no-patch {range_str}").split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    os.chdir(script_path)
    util.check_result_throw(result)

    decoded_stdout = util.try_decode(result.stdout)
    if decoded_stdout is not None:
        return [x.strip("'\"") for x in decoded_stdout.splitlines()]
    else:
        return []


def get_commits_by_range(cache_dir, from_ref, to_ref):
    update_info_repo(cache_dir)
    repo_info = os.path.join(cache_dir, "./repo_info")
    return get_commits_raw(repo_info, f"{from_ref}..{to_ref}")


def get_commits_by_branch_and_num(cache_dir, branch, num):
    update_info_repo(cache_dir)
    repo_info = os.path.join(cache_dir, "./repo_info")
    return get_commits_raw(repo_info, f"{branch} -{num}")

def get_current_commit(dir):
    return get_commits_raw(".", f"-n 1")[0]

def clone_and_build(commit,
                    cache_dir,
                    remote="VowpalWabbit",
                    build_overrides=None):
    commits_repos_dir = Path(os.path.join(cache_dir, "clones", f"{remote}-{commit}")).resolve()
    print(commits_repos_dir)
    if os.path.exists(commits_repos_dir):
        print(f"Skipping {remote}-{commit} - already exists")
    else:
        update_info_repo(cache_dir)
        print(f"Cloning {remote}-{commit}...")
        if(remote == "VowpalWabbit"):
            util.check_result_throw(
                subprocess.run(
                    (f"git clone ./repo_info {commits_repos_dir}").split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, cwd=cache_dir))
        else:
            util.check_result_throw(
                subprocess.run(
                    (f"git clone https://github.com/{remote}/vowpal_wabbit/ {commits_repos_dir}").split(),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, cwd=cache_dir))
        os.chdir(commits_repos_dir)
        print(f"Checking out {remote}-{commit}...")
        util.check_result_throw(
            subprocess.run((f"git checkout {commit}").split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT))
        print(f"Building {remote}-{commit}...")
        if build_overrides is not None and commit in build_overrides:
            commands = build_overrides[commit]
            print(f"Running custom build for {remote}-{commit}...")
            for command in commands:
                print(f"Running build step '{command}' for {remote}-{commit}...")
                util.check_result_throw(
                    subprocess.run(command,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT))
        else:
            print(f"Running default build for {remote}-{commit}...")
            util.check_result_throw(
                subprocess.run(["make"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT))
        print(f"Finished with {remote}-{commit}")
        os.chdir(script_path)
    return commits_repos_dir


# Not platform independent. Assumes bash or bashlike as shell.
FORCE_RELEASE_BUILD_COMMANDS: str = "mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. "
f"&& make -j{multiprocessing.cpu_count()} vw-bin"

BUILD_OVERRIDES = {"860ccc5c": [FORCE_RELEASE_BUILD_COMMANDS]}

def resolve_args_to_commit_list(cache_dir, commits, num, from_ref, to_ref):
    if commits is not None:
        return commits
    elif num is not None:
        return get_commits_by_branch_and_num(cache_dir, "master", num)
    elif from_ref is not None and to_ref is not None:
        return get_commits_by_range(cache_dir, from_ref, to_ref)
    else:
        print("Error: either commits, num or from and to must be supplied")
        exit(1)


def run(commits, num, from_ref, to_ref, cache_dir):
    commits_to_process = resolve_args_to_commit_list(cache_dir, commits, num, from_ref,
                                                     to_ref)

    for commit in commits_to_process:
        commits_repos_dir = os.path.realpath(os.path.join(cache_dir, "./clones/", commit))
        try:
            clone_and_build(commit, cache_dir, remote="VowpalWabbit", build_overrides=BUILD_OVERRIDES)
        except util.CommandFailed as e:
            print(f"Skipping {commit}, failed with: {e}")
            # print(f"stdout: {e.stdout}")
            # print(f"stderr: {e.stderr}")
            shutil.rmtree(commits_repos_dir)
