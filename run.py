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
import data
import textwrap

def make_command_line_test(vw_bin, command_line):
  def command_line_test():
    util.check_result_throw(subprocess.run((vw_bin + " " + command_line).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT))
  return command_line_test, command_line

# Add functions here that will run as part of the harness. They should return the time in seconds it took to run it.
def get_steps(vw_bin):
  return [
    make_command_line_test(vw_bin, "--no_stdin"),
    make_command_line_test(vw_bin, "-d ./data/rcv1/rcv1/rcv1.train.vw.gz -f r_temp"),
    # This specific test must run after the previous test as it uses the produced model.
    make_command_line_test(vw_bin, "-d ./data/rcv1/rcv1/rcv1.test.vw.gz -t -i r_temp"),
    make_command_line_test(vw_bin, "-t --dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
    make_command_line_test(vw_bin, "--dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
  ]

def run_harness(vw_bin, num_runs, step_generator = get_steps):
  benchmarks = []
  steps = step_generator(vw_bin)
  for step, name in steps:
    print("\trunning bench: '{}'".format(name))

    runs = []
    # Average over number of runs
    for _ in range(num_runs):
      start_time = time.perf_counter()
      # Run the step
      step()
      end_time = time.perf_counter()
      runs.append(end_time - start_time)
    benchmarks.append({
      "vw_bin" : vw_bin,
      "name" : name,
      "runs" : runs
      })
  return benchmarks

def run(bins, clone_dir, num_runs, num, skip_existing):
  bin_name = "vw"
  if bins is not None:
    bins = bins
  elif clone_dir is not None:
    print("Searching for {} in {}".format(bin_name, clone_dir))
    bins = find.find_all(bin_name, clone_dir)
    print("found {} binaries".format(len(bins)))
  elif num is not None:
    commits_to_process = clone.get_commits("master", num)
    bins = []
    for commit in commits_to_process:
      commit_path = os.path.realpath(os.path.join("./clones/", commit))
      if not os.path.exists(commit_path):
        print("{} does not exist. Please checkout and build using `python3 run.py clone --commits {}`".format(commit, commit))
      bins.extend(find.find_all(bin_name, commit_path))
  else:
    print("Error: etiher bins, clone_dir or num must be supplied.")
    exit(1)

  if os.path.exists('data.json'):
    with open('data.json') as f:
      perf_info = json.load(f)
  else:
    perf_info = {}

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
      else:
        print("Skipping {} found - skipping")
        continue

      # Save commit info
      perf_info[ref]["commit"] = ref
      perf_info[ref]["date"] = clone.get_commit_date(ref)

      # Run harness
      benchmarks = run_harness(os.path.realpath(vw_bin), num_runs, get_steps)

      # Record benchmark info
      if "benchmarks" not in perf_info[ref]:
        perf_info[ref]["benchmarks"] = {}
      for bnch in benchmarks:
        if bnch["name"] not in perf_info[ref]["benchmarks"]:
          perf_info[ref]["benchmarks"][bnch["name"]] = {}
        perf_info[ref]["benchmarks"][bnch["name"]]["bin"] = bnch["vw_bin"]
        perf_info[ref]["benchmarks"][bnch["name"]]["name"] = bnch["name"]
        if "runs" not in perf_info[ref]["benchmarks"][bnch["name"]]:
          perf_info[ref]["benchmarks"][bnch["name"]]["runs"] = []
        perf_info[ref]["benchmarks"][bnch["name"]]["runs"].extend(bnch["runs"])
        perf_info[ref]["benchmarks"][bnch["name"]]["average"] = sum(perf_info[ref]["benchmarks"][bnch["name"]]["runs"]) / len(perf_info[ref]["benchmarks"][bnch["name"]]["runs"])

      # Save as we go in case of quit/crash
      with open('data.json', 'w') as f:
        json.dump(perf_info, f)

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
      subcommands:
        run\t\tMain perf testing harness
        prepare\tDownloads and extracts required datasets for perf harness
        clone\t\tUtility to clone and build commits in expected directory structure
        find\t\tUsed to find binaries in a directory (not important)

      Use `<subcommand> -h` to see usage of a subcommand
      ''')
  )
  subparsers = parser.add_subparsers(dest='command')

  run_parser = subparsers.add_parser("run")
  clone_parser = subparsers.add_parser("clone")
  prepare_parser = subparsers.add_parser("prepare")
  find_parser = subparsers.add_parser("find")
  data_parser = subparsers.add_parser("merge")

  run_group = run_parser.add_mutually_exclusive_group(required=True)
  run_group.add_argument("--bins", help="Paths to VW binaries to test", type=str, nargs='+', default=None)
  run_group.add_argument("--clone_dir", help="Path to search for vw binaries", type=str, default=None)
  run_group.add_argument("--num", help="Number of commits back in history to test", type=int, default=None)
  run_parser.add_argument("--runs", help="How many runs to average over", default=1, type=int)
  run_parser.add_argument("--skip_existing", help="Skip over commits already done", default=True, type=bool)

  clone_group = clone_parser.add_mutually_exclusive_group(required=True)
  clone_group.add_argument('--commits', type=str, nargs='+',
                    help='List of all commits to checkout', default=None)
  clone_group.add_argument('--num', type=int,
                    help='Number of master commits into past to checkout', default=None)

  find_parser.add_argument("--name", help="Binary name to find")
  find_parser.add_argument("--path", help="Path to find in", default="./clones/")

  data_parser.add_argument("--files", help="Data files to merge", type=str, nargs='+', default=[], required=True)
  data_parser.add_argument("--merged_name", help="Name of merged file", type=str, default="merged.json")

  args = parser.parse_args()

  # Check if a command was supplied
  if args.command is None:
    parser.print_help()
    exit(1)
  elif args.command == "clone":
    clone.run(args.commits, args.num)
  elif args.command == "prepare":
    prepare.run()
  elif args.command == "run":
    run(args.bins, args.clone_dir, args.runs, args.num, args.skip_existing)
  elif args.command == "find":
    find.run(args.bin_name, args.path)
  elif args.command == "merge":
    data.merge(args.files, args.merged_name)
