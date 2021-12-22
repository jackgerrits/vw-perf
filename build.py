import subprocess
import util
import shlex
from pathlib import Path
from typing import List

def get_commit_info(repo_dir: Path, commit: str):
    result = subprocess.run(
        ["git","log",commit,"--date=iso","--pretty=%an;%s;%ad","-1"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    info = util.try_decode(result.stdout).splitlines()[0].split(";")

    # Javascript can't seem to parse the date when there is a space between time and timezone, remove it.
    space_index = info[2].rfind(' ')
    info[2] = info[2][:space_index] + info[2][space_index + 1:]

    return {"author": info[0], "title": info[1], "date": info[2], "ref": commit}


def get_commits_raw(repo_dir: Path, range_str: str) -> List[str]:
    args = ["git", "log", '--pretty=format:"%H"', "--no-patch"]
    args.extend(shlex.split(range_str))
    result = subprocess.run(args
        , cwd=repo_dir, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)
    decoded_stdout = util.try_decode(result.stdout)
    if decoded_stdout is not None:
        return [x.strip("'\"") for x in decoded_stdout.splitlines()]
    else:
        return []

def get_commits_by_range(repo_dir: Path, from_ref: str, to_ref: str) -> List[str]:
    fetch_repo_upstream(repo_dir)
    return get_commits_raw(repo_dir, f"{from_ref}..{to_ref}")


def get_commits_by_branch_and_num(repo_dir: Path, branch: str, num: int) -> List[str]:
    fetch_repo_upstream(repo_dir)
    return get_commits_raw(repo_dir, f"{branch} -{num}")

def build_binary(repo_dir: Path) -> Path:
    subprocess.run(["cmake", "-B", repo_dir/"build", "-S", repo_dir, "-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release"],stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)
    subprocess.run(["cmake", "--build", repo_dir/"build", "--target", "vw-bin"],stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)
    vw_binary = repo_dir/"build"/"vowpalwabbit"/"vw"
    if not vw_binary.is_file():
        raise ValueError("vw binary not found")
    return vw_binary

def clean_repo(repo_dir: Path) -> None:
    subprocess.run(["git", "clean", "-xdf", "."], cwd=repo_dir, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=repo_dir, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)

def checkout_commit(repo_dir: Path, commit: str) -> None:
    subprocess.run(["git", "checkout", commit], cwd=repo_dir, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)

def fetch_repo_upstream(repo_dir: Path):
    subprocess.run(["git", "checkout", "master"], cwd=repo_dir, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)
    subprocess.run(["git", "pull", "origin", "master"], cwd=repo_dir, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, check=True)

if __name__ == "__main__":
    binary_dir = Path("./binaries/")
    binary_dir.mkdir(parents=True, exist_ok=True)

    repo_dir = Path("../vowpal_wabbit")
    commit_range = get_commits_by_branch_and_num(repo_dir, "master", 2)
    for commit in commit_range:
        destination_binary_file = binary_dir / f"vw-{commit}"
        if destination_binary_file.is_file():
            print(f"{commit} already exists. Skipping...")
            continue
        print(f"Building {commit}...")
        clean_repo(repo_dir)
        checkout_commit(repo_dir, commit)
        produced_binary = build_binary(repo_dir)
        produced_binary.rename(destination_binary_file)