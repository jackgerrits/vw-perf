"""This module defines helpers for cloning, building and resolving commits"""

import os
import time
import subprocess
import util
import shutil
import multiprocessing

import sys

from typing import List
script_path = os.path.abspath(os.path.dirname(sys.argv[0]))


def get_commit_info(commit):
    repo_info = "./repo_info"
    if not os.path.exists(repo_info):
        print(f"Cloning {commit}...")
        util.check_result_throw(
            subprocess.run((
                f"git clone https://github.com/VowpalWabbit/vowpal_wabbit/ {repo_info}"
            ).split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT))

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

    return {"author": info[0], "title": info[1], "date": info[2]}


def update_info_repo(branch: str = "master") -> None:
    repo_info = "./repo_info"
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


def get_commits_raw(range_str: str) -> List[str]:
    update_info_repo()
    repo_info = "./repo_info"
    os.chdir(repo_info)
    result = subprocess.run(
        (f"git log --pretty=format:\"%h\" --no-patch {range_str}").split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    os.chdir(script_path)
    util.check_result_throw(result)

    decoded_stdout = util.try_decode(result.stdout)
    if decoded_stdout is not None:
        return [x.strip("'\"") for x in decoded_stdout.splitlines()]
    else:
        return []


def get_commits_by_range(from_ref, to_ref):
    return get_commits_raw(f"{from_ref}..{to_ref}")


def get_commits_by_branch_and_num(branch, num):
    return get_commits_raw(f"{branch} -{num}")


def clone_and_build(commit,
                    build_overrides=None,
                    clone_dir: str = "./clones/"):
    commits_repos_dir = os.path.join(clone_dir, commit)
    if os.path.exists(commits_repos_dir):
        print(f"Skipping {commit} - already exists")
    else:
        update_info_repo()
        print(f"Cloning {commit}...")
        util.check_result_throw(
            subprocess.run(
                (f"git clone ./repo_info {commits_repos_dir}").split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT))
        os.chdir(commits_repos_dir)
        print(f"Checking out {commit}...")
        util.check_result_throw(
            subprocess.run((f"git checkout {commit}").split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT))
        print(f"Building {commit}...")
        if build_overrides is not None and commit in build_overrides:
            commands = build_overrides[commit]
            print(f"Running custom build for {commit}...")
            for command in commands:
                print(f"Running build step '{command}' for {commit}...")
                util.check_result_throw(
                    subprocess.run(command,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT))
        else:
            print(f"Running default build for {commit}...")
            util.check_result_throw(
                subprocess.run(["make"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT))
        print(f"Finished with {commit}")
        os.chdir(script_path)


# Not platform independent. Assumes bash or bashlike as shell.
FORCE_RELEASE_BUILD_COMMANDS: str = "mkdir build && cd build && cmake -DCMAKE_BUILD_TYPE=Release .. "
f"&& make -j{multiprocessing.cpu_count()} vw-bin"

BUILD_OVERRIDES = {"860ccc5c": [FORCE_RELEASE_BUILD_COMMANDS]}


def resolve_args_to_commit_list(commits, num, from_ref, to_ref):
    if commits is not None:
        return commits
    elif num is not None:
        return get_commits_by_branch_and_num("master", num)
    elif from_ref is not None and to_ref is not None:
        return get_commits_by_range(from_ref, to_ref)
    else:
        print("Error: either commits, num or from and to must be supplied")
        exit(1)


def run(commits, num, from_ref, to_ref):
    commits_to_process = resolve_args_to_commit_list(commits, num, from_ref,
                                                     to_ref)

    for commit in commits_to_process:
        commits_repos_dir = os.path.realpath(os.path.join("./clones/", commit))
        try:
            clone_and_build(commit, BUILD_OVERRIDES, "./clones/")
        except util.CommandFailed as e:
            print(f"Skipping {commit}, failed with: {e}")
            # print(f"stdout: {e.stdout}")
            # print(f"stderr: {e.stderr}")
            shutil.rmtree(commits_repos_dir)
