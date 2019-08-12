import os
import time
import argparse
import subprocess
import util
import find
import clone
import json
import prepare
import find
import textwrap

def make_command_line_test(vw_bin, command_line):
  def command_line_test():
    util.check_result_throw(subprocess.run((vw_bin + " " + command_line).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
  return command_line_test, command_line

def get_steps(vw_bin):
  # Add functions here that will run as part of the harness. They should return the time in seconds it took to run it.
  return [
    make_command_line_test(vw_bin, "--no_stdin"),
    make_command_line_test(vw_bin, "--no_stdin -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t"),
    make_command_line_test(vw_bin, "-d ./data/rcv1/rcv1/rcv1.train.vw.gz -f r_temp"),
    # This specific test must run after the previous test as it uses the produced model.
    make_command_line_test(vw_bin, "-d ./data/rcv1/rcv1/rcv1.test.vw.gz -t -i r_temp"),
    make_command_line_test(vw_bin, "-t --dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
    make_command_line_test(vw_bin, "--dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
  ]

def get_quick_steps(vw_bin):
  # Add functions here that will run as part of the harness. They should return the time in seconds it took to run it.
  return [
    make_command_line_test(vw_bin, "--no_stdin"),
    make_command_line_test(vw_bin, "--no_stdin -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t"),
  ]

class Benchmark():
  def __init__(self, vw_bin, name, runs, runtime_in_sec, commit = None, date = None):
    self.vw_bin = vw_bin
    self.name = name
    self.runs = runs
    self.runtime_in_sec = runtime_in_sec
    self.commit = commit
    self.date = date

  def avg(self):
    return self.runtime_in_sec / self.runs

def run_harness(vw_bin, runs, step_generator = get_steps):
  benchmarks = []
  steps = step_generator(vw_bin)
  for step, name in steps:
    run_time_in_sec = 0
    print("\trunning bench: '{}'".format(name))


    # Average over number of runs
    for _ in range(runs):
      start_time = time.perf_counter()
      # Run the step
      step()
      end_time = time.perf_counter()
      run_time_in_sec += end_time - start_time
    benchmarks.append(Benchmark(vw_bin, name, runs, run_time_in_sec))
  return benchmarks

def run_harness_with_commit_info(vw_bin, runs, step_generator = get_steps):
  benchmarks = []
  steps = step_generator(vw_bin)
  try:
    ref = find.extract_ref(vw_bin)
    date = clone.get_commit_date(ref)
  except Exception as e:
    ref = "unknown"
    date = "unknown"

  for step, name in steps:
    run_time_in_sec = 0
    try:
      # Average over number of runs
      for _ in range(runs):
        start_time = time.perf_counter()
        # Run the step
        step()
        end_time = time.perf_counter()
        run_time_in_sec += end_time - start_time
      benchmarks.append(Benchmark(vw_bin, name, runs, run_time_in_sec, ref, date))
    except Exception as e:
      benchmarks.append(Benchmark(vw_bin, name, -1, -1, ref, date))
  return benchmarks

def run(bins, clone_dir, runs):
  if bins is not None:
    bins = bins
  elif clone_dir is not None:
    bins = find.find_all("vw", clone_dir)
  else:
    print("Error: etiher bins or clone_dir must be supplied.")
    parser.print_help()
    exit(1)

  with open('data.json') as f:
    perf_info = json.load(f)

  for vw_bin in bins:
    try:
      ref = find.extract_ref(vw_bin)
    except util.CommandFailed as e:
      print("Skipping {}, failed with: {}".format(vw_bin, e))
      continue

    print("Testing {}".format(ref))

    try:
      if ref not in perf_info:
        perf_info[ref] = {}
      perf_info[ref]["commit"] = ref
      perf_info[ref]["commit"] = ref
      perf_info[ref]["date"] = clone.get_commit_date(ref)
      benchmarks = run_harness(os.path.realpath(vw_bin), runs, get_steps)
      if "benchmarks" not in perf_info[ref]:
        perf_info[ref]["benchmarks"] = {}
      for bnch in benchmarks:
        if bnch.name not in perf_info[ref]["benchmarks"]:
          perf_info[ref]["benchmarks"][bnch.name] = {}
        perf_info[ref]["benchmarks"][bnch.name]["bin"] = bnch.vw_bin
        perf_info[ref]["benchmarks"][bnch.name]["name"] = bnch.name
        perf_info[ref]["benchmarks"][bnch.name]["runs"] = bnch.runs
        perf_info[ref]["benchmarks"][bnch.name]["runtime_in_sec"] = bnch.runtime_in_sec
        perf_info[ref]["benchmarks"][bnch.name]["average"] = bnch.avg()
        # print("{},{},{},{},{}".format(bnch.vw_bin, bnch.name, bnch.runs, bnch.runtime_in_sec, bnch.avg()))
    except util.CommandFailed as e:
      perf_info.pop(ref, None)
      print("Skipping {}, failed with: {}".format(ref, e))
      continue
  with open('data.json', 'w') as f:
    json.dump(perf_info, f)

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    "run.py",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description=textwrap.dedent('''\
      commands:
        run\t\tMain perf testing harness
        prepare\tDownloads and extracts required datasets for perf harness
        clone\t\tUtility to clone and build commits in expected directory structure
        find\t\tUsed to find binaries in a directory (not important)
      ''')
  )
  subparsers = parser.add_subparsers(dest='command')

  run_parser = subparsers.add_parser("run")
  clone_parser = subparsers.add_parser("clone")
  prepare_parser = subparsers.add_parser("prepare")
  find_parser = subparsers.add_parser("find")

  run_parser.add_argument("--bins", help="Paths to VW binaries to test", type=str, nargs='+')
  run_parser.add_argument("--clone_dir", help="Path to search for vw binaries", type=str)
  run_parser.add_argument("--runs", help="How many runs to average over", default=1, type=int)

  clone_parser.add_argument('tags_or_shas', type=str, nargs='+',
                    help='List of all tags or shas to checkout')

  find_parser.add_argument("bin_name", help="Binary name to find")
  find_parser.add_argument("--path", help="Path to find in", default="./clones/")

  args = parser.parse_args()

  # Check if a command was supplied
  if args.command is None:
    parser.print_help()
    exit(1)
  elif args.command == "clone":
    clone.run(args.tags_or_shas)
  elif args.command == "prepare":
    prepare.run()
  elif args.command == "run":
    run(args.bins, args.clone_dir, args.runs)
  elif args.command == "run":
    find.run(args.bin_name, args.path)
