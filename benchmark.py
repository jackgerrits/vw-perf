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

BenchmarkDefinition = Tuple[Callable[[], float], str]

def make_command_line_test(
        vw_bin: str, command_line: str, benchmark_name=None, cwd=None) -> Tuple[Callable[[], None], str]:
    def command_line_test():
        start_time = time.perf_counter()
        util.check_result_throw(
            subprocess.run((vw_bin + " " + command_line).split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, cwd=cwd))
        end_time = time.perf_counter()
        return end_time - start_time
    if benchmark_name is None:
        benchmark_name = command_line
    return command_line_test, benchmark_name

def make_command_line_test_with_cache(
        vw_bin: str, cache_file_name: str, command_line_to_generate_cache: str, command_line: str, benchmark_name=None, cwd=None) -> BenchmarkDefinition:
    def command_line_test():
        # If the cache file is not existant, run the command to generate it
        if not os.path.exists(cache_file_name):
            util.check_result_throw(
                subprocess.run((vw_bin + " " + command_line_to_generate_cache).split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, cwd=cwd))

        start_time = time.perf_counter()
        util.check_result_throw(
            subprocess.run((vw_bin + " " + command_line).split(),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, cwd=cwd))
        end_time = time.perf_counter()
        return end_time - start_time
    if benchmark_name is None:
        benchmark_name = command_line
    return command_line_test, benchmark_name


def get_steps(cache_dir: str, working_dir: str, vw_bin: str) -> List[BenchmarkDefinition]:
    """Add functions here that will run as part of the harness. They should return the time in
    seconds it took to run it.
    """
    return [
         make_command_line_test(
            vw_bin,
            f"-d {cache_dir}/data/cb_data/cb_data.dsjson --onethread --cb_explore_adf --noop",
            benchmark_name = "-d cb_data.dsjson --onethread --cb_explore_adf --noop"
        ),
        make_command_line_test(
            vw_bin,
            f"-d {cache_dir}/data/rcv1/rcv1.train.vw --onethread --noop",
            benchmark_name = "-d rcv1.train.vw --onethread --noop"
        ),
        make_command_line_test_with_cache(
            vw_bin,
            f"{working_dir}/rcv1.train.vw.cache",
            f"--cache_file {working_dir}/rcv1.train.vw.cache -d {cache_dir}/data/rcv1/rcv1.train.vw",
            f"--cache_file {working_dir}/rcv1.train.vw.cache -d {cache_dir}/data/rcv1/rcv1.train.vw --onethread --passes 5 -f {working_dir}/rcv1_model",
            benchmark_name = "--cache_file rcv1.train.vw.cache -d rcv1.train.vw --onethread --passes 5 -f rcv1_model"
        ),
        # This specific test must run after the previous test as it uses the produced model.
        make_command_line_test_with_cache(
            vw_bin,
            f"{working_dir}/rcv1.test.vw.cache",
            f"--cache_file {working_dir}/rcv1.test.vw.cache -d {cache_dir}/data/rcv1/rcv1.test.vw",
            f"--cache_file {working_dir}/rcv1.test.vw.cache -d {cache_dir}/data/rcv1/rcv1.test.vw -t --onethread --passes 5 -i {working_dir}/rcv1_model",
            benchmark_name = "--cache_file rcv1.test.vw.cache -d rcv1.test.vw -t --onethread --passes 5 -i rcv1_model"
        ),
        make_command_line_test_with_cache(
            vw_bin,
            f"{working_dir}/cb_data.dsjson.cache",
            f"--cache_file {working_dir}/cb_data.dsjson.cache -d {cache_dir}/data/cb_data/cb_data.dsjson --dsjson --cb_explore_adf",
            f"--cache_file {working_dir}/cb_data.dsjson.cache -d {cache_dir}/data/cb_data/cb_data.dsjson --onethread --cb_explore_adf --passes 5 -q UB --epsilon 0.2 -l 0.5 --power_t 0 -f {working_dir}/cb_model",
            benchmark_name = "--cache_file cb_data.dsjson.cache -d cb_data.dsjson --onethread --cb_explore_adf --passes 5 -q UB --epsilon 0.2 -l 0.5 --power_t 0 -f cb_model"
        ),
        # This specific test must run after the previous test as it uses the produced model.
        make_command_line_test_with_cache(
            vw_bin,
            f"{working_dir}/cb_data.dsjson.cache",
            f"--cache_file {working_dir}/cb_data.dsjson.cache -d {cache_dir}/data/cb_data/cb_data.dsjson --dsjson --cb_explore_adf",
            f"--cache_file {working_dir}/cb_data.dsjson.cache -d {cache_dir}/data/cb_data/cb_data.dsjson -t --onethread --cb_explore_adf --passes 5 -q UB --epsilon 0.2 -l 0.5 --power_t 0 -i {working_dir}/cb_model",
            benchmark_name = "-cache_file cb_data.dsjson.cache -d cb_data.dsjson -t --onethread --cb_explore_adf --passes 5 -q UB --epsilon 0.2 -l 0.5 --power_t 0 -i cb_model"
        ),
    ]


def run_harness(cache_dir: str,
                vw_bin: str,
                num_runs: int,
                step_generator: Callable[[str,str,str], List[BenchmarkDefinition]], quiet=False):
    binary_hash = util.get_file_hash(vw_bin)

    working_dir = os.path.join(cache_dir, binary_hash)
    if not os.path.exists(working_dir):
        os.mkdir(working_dir)
    
    benchmarks = []
    steps = step_generator(cache_dir, working_dir, vw_bin)
    for step, name in steps:
        if not quiet:
            print(f"Running bench: '{name}'", end ="")

        runs = []
        # Average over number of runs
        for i in range(num_runs):
            if not quiet:
                print(f"\rRunning bench: '{name}', run {i}/{num_runs}",end ="")
            
            # Run the step
            duration = -1
            try:
                duration = step()
            except util.CommandFailed as e:
                print()
                print(e)
                print(e.stderr)
                print(e.stdout)
                raise
            runs.append(duration)
        benchmarks.append({"vw_bin": vw_bin, "name": name, "runs": runs})
        if not quiet:
            print(f"\rRunning bench: '{name}', run {num_runs}/{num_runs} - Done")
    return benchmarks


class PerfInfo:
    def __init__(self, json_data=None):
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
            benchmarks = run_harness(cache_dir, os.path.realpath(vw_bin), num_runs, get_steps)

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
    test_benchmarks = run_harness(cache_dir, os.path.realpath(vw_bin_to_test), num_runs, get_steps, quiet=False)
    print(f"Running reference benchmarks on '{reference_binary}'...")
    reference_benchmarks = run_harness(cache_dir, os.path.realpath(reference_binary), num_runs, get_steps, quiet=False)

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

    formatted_table = tabulate(table, headers=["name", "number of runs", "test mean (s)", "reference mean (s)", "difference (s)", "difference (%)"])
    print(formatted_table)

    tsv_formatted_table = tabulate(table, headers=["name", "number of runs", "test mean (s)", "reference mean (s)", "difference (s)", "difference (%)"], tablefmt="tsv")
    with open("results.tsv","w") as text_file:
        text_file.write(tsv_formatted_table)

