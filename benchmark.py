import os
import time
import subprocess
import json
import textwrap

import util
import find
import clone
import statistics

import sys

from tabulate import tabulate

from typing import Callable, Tuple, List, Union, TextIO, Optional, Any, Dict


def make_command_line_test(
        vw_bin: str, command_line: str) -> Tuple[Callable[[], None], str]:
    def command_line_test():
        util.check_result_throw(
            subprocess.run((vw_bin + " " + command_line).split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT))

    return command_line_test, command_line


def gen_steps(cache_dir):
    def get_steps(vw_bin: str) -> List[Tuple[Callable[[], None], str]]:
        """Add functions here that will run as part of the harness. They should return the time in
        seconds it took to run it.
        """
        return [
            # make_command_line_test(vw_bin, "--no_stdin"),
            # make_command_line_test(
            #     vw_bin, f"-d {cache_dir}/data/rcv1/rcv1/rcv1.train.vw.gz -f r_temp"),
            # This specific test must run after the previous test as it uses the produced model.
            make_command_line_test(
                vw_bin, f"-d {cache_dir}/data/rcv1/rcv1/rcv1.test.vw.gz -t -i r_temp")
            # make_command_line_test(
            #     vw_bin,
            #     f"-t --dsjson -d {cache_dir}/data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB "
            #     "--epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
            # make_command_line_test(
            #     vw_bin,
            #     f"--dsjson -d {cache_dir}/data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB "
            #     "--epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
        ]
    return get_steps


def run_harness(vw_bin: str,
                num_runs: int,
                step_generator: Callable[[str], List[Tuple[Callable[[], None],
                                                           str]]], quiet=False):
    benchmarks = []
    steps = step_generator(vw_bin)
    for step, name in steps:
        if not quiet:
            print(f"Running bench: '{name}'", end ="")

        runs = []
        # Average over number of runs
        for i in range(num_runs):
            if not quiet:
                print(f"\rRunning bench: '{name}', run {i}/{num_runs}",end ="")
            start_time = time.perf_counter()
            # Run the step
            step()
            end_time = time.perf_counter()
            runs.append(end_time - start_time)
        benchmarks.append({"vw_bin": vw_bin, "name": name, "runs": runs})
        if not quiet:
            print(f"\rRunning bench: '{name}', run {num_runs}/{num_runs} - Done")
    return benchmarks


class PerfInfo:
    def __init__(self, json_data=Optional[Dict[str, Any]]):
        if json_data is not None:
            self.perf_data = json_data
        else:
            self.perf_data = {}

    @staticmethod
    def from_file(file_name):
        with open('data.json') as f:
            return PerfInfo(json.load(f))

    @staticmethod
    def from_string(json_string):
        return PerfInfo(json.loads(json_string))

    def ref_exists(self, commit_ref: str) -> bool:
        return commit_ref in self.perf_data

    def set_ref_info(self, commit_ref: str, author, title, date):
        if not self.ref_exists(commit_ref):
            self.perf_data[commit_ref] = {}

        self.perf_data[commit_ref]["author"] = author
        self.perf_data[commit_ref]["title"] = title
        self.perf_data[commit_ref]["date"] = date

    def remove_ref(self, commit_ref):
        self.perf_data.pop(commit_ref, None)

    def add_benchmark_data(self, commit_ref, benchmark_name, runs):
        if "benchmarks" not in self.perf_data[commit_ref]:
            self.perf_data[commit_ref]["benchmarks"] = {}

        if benchmark_name not in self.perf_data[commit_ref]["benchmarks"]:
            self.perf_data[commit_ref]["benchmarks"][benchmark_name] = {}

        if "runs" not in self.perf_data[commit_ref]["benchmarks"][
                benchmark_name]:
            self.perf_data[commit_ref]["benchmarks"][benchmark_name][
                "runs"] = []

        self.perf_data[commit_ref]["benchmarks"][benchmark_name][
            "name"] = benchmark_name
        self.perf_data[commit_ref]["benchmarks"][benchmark_name][
            "runs"].extend(runs)
        self.perf_data[commit_ref]["benchmarks"][benchmark_name][
            "average"] = sum(self.perf_data[commit_ref]["benchmarks"]
                             [benchmark_name]["runs"]) / len(
                                 self.perf_data[commit_ref]["benchmarks"]
                                 [benchmark_name]["runs"])

    def save_to_file(self, file_name: str):
        with open(file_name, 'w') as f:
            json.dump(self.perf_data, f)


def run(commits, num, from_ref, to_ref, num_runs, skip_existing, cache_dir):
    COMMITS_REPOS_DIR = os.path.join(cache_dir,"./clones/")
    BIN_NAME = "vw"
    commits_to_process = clone.resolve_args_to_commit_list(
        cache_dir, commits, num, from_ref, to_ref)

    commits_and_bins = []
    for commit in commits_to_process:
        commit_path = os.path.realpath(os.path.join(COMMITS_REPOS_DIR, commit))
        if not os.path.exists(commit_path):
            print(
                "{commit} does not exist. Please checkout and build using `python3 run.py clone "
                f"--commits {commit}`")
        vw_bins = find.find_all(BIN_NAME, commit_path)
        commits_and_bins.append((commit, vw_bins[0]))

    if os.path.exists('data.json'):
        perf_info = PerfInfo.from_file('data.json')
    else:
        perf_info = PerfInfo()

    for ref, vw_bin in commits_and_bins:
        print(f"Testing {ref}")

        try:
            if perf_info.ref_exists(ref) and skip_existing == True:
                print(f"Skipping {ref} found - skipping")
                continue

            # Run harness
            benchmarks = run_harness(os.path.realpath(vw_bin), num_runs,
                                     gen_steps(cache_dir))

            # Save commit info
            info = clone.get_commit_info(cache_dir, ref)
            perf_info.set_ref_info(ref, info["author"], info["title"],
                                   info["date"])

            # Record benchmark info
            for bnch in benchmarks:
                perf_info.add_benchmark_data(ref, bnch["name"], bnch["runs"])

            # Save as we go in case of quit/crash
            perf_info.save_to_file("data.json")

        except util.CommandFailed as e:
            perf_info.remove_ref(ref)
            print(f"Skipping {ref}, failed with: {e}")
            continue
    perf_info.save_to_file("data.json")

def run_for_binary(vw_bin_to_test, reference_binary, num_runs, cache_dir):
    """If binary is None, search for it"""

    # TODO: support if reference_binary is None

    DATA_DIR = os.path.join(cache_dir, "./data/")
    if not os.path.exists(DATA_DIR):
        print("Data directory not found - run: `python .\\run.py prepare`")
        sys.exit(1)
            
    ref_info = None
    try:
        ref_info = clone.get_commit_info(cache_dir, clone.get_current_commit(cache_dir))
    except util.CommandFailed:
        print("Warning: Commit info could not be found. Are you inside the vowpal_wabbit git repo?")

    print(f"Running test benchmarks on '{vw_bin_to_test}'...")
    test_benchmarks = run_harness(os.path.realpath(vw_bin_to_test), num_runs, gen_steps(cache_dir), quiet=False)
    print(f"Running reference benchmarks on '{reference_binary}'...")
    reference_benchmarks = run_harness(os.path.realpath(reference_binary), num_runs, gen_steps(cache_dir), quiet=False)
    
    if ref_info:
        print(ref_info)
    else:
        print("No commit info available")

    # TODO support extended statistics
    table = []
    for test_bench, reference_bench in zip(test_benchmarks, reference_benchmarks):
        test_mean = statistics.mean(test_bench["runs"])
        # test_median = statistics.median(test_bench["runs"])
        # test_stdev = statistics.pstdev(test_bench["runs"])
        reference_mean = statistics.mean(reference_bench["runs"])
        # reference_median = statistics.median(reference_bench["runs"])
        # reference_stdev = statistics.pstdev(reference_bench["runs"])
        table.append([test_bench["name"], num_runs, test_mean, reference_mean, test_mean - reference_mean, (test_mean - reference_mean) / reference_mean*100])
 
    print(tabulate(table, headers=["name", "number of runs", "test mean (s)", "reference mean (s)", "difference (s)", "difference (%)"]))
