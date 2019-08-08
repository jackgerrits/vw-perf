import os
import time
import argparse
import subprocess

def check_result(result):
  if(result.returncode != 0):
    print(result.args)
    if result.stderr is not None:
      print(result.stderr.decode("utf-8"))
    if result.stdout is not None:
      print(result.stdout.decode("utf-8"))
    exit(1)

def make_command_line_test(vw_bin, command_line):
  def command_line_test():
    result = subprocess.run((vw_bin + " " + command_line).split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    check_result(result)

  return command_line_test, command_line

def harness(vw_bin, runs):
  # Add functions here that will run as part of the harness. They should return the time in seconds it took to run it.
  steps = [
    make_command_line_test(vw_bin, "--no_stdin"),
    make_command_line_test(vw_bin, "--no_stdin -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t"),
    make_command_line_test(vw_bin, "-d ./data/rcv1/rcv1/rcv1.train.vw.gz -f r_temp"),
    # This specific test must run after the previous test as it uses the produced model.
    make_command_line_test(vw_bin, "-d ./data/rcv1/rcv1/rcv1.test.vw.gz -t -i r_temp"),
    make_command_line_test(vw_bin, "-t --dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
    make_command_line_test(vw_bin, "--dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0"),
  ]

  print("test,runs,total,average")
  for step, name in steps:
    run_time_in_sec = 0

    # Average over number of runs
    for _ in range(runs):
      start_time = time.perf_counter()
      # Run the step
      step()
      end_time = time.perf_counter()
      run_time_in_sec += end_time - start_time

    print("{},{},{},{}".format(name, runs, run_time_in_sec, run_time_in_sec/runs))

if __name__ == '__main__':
  parser = argparse.ArgumentParser("Perf harness")
  parser.add_argument("bin", help="Path to VW binary to test")
  parser.add_argument("--runs", help="How many runs to average over", default=1, type=int)
  args = parser.parse_args()

  harness(os.path.realpath(args.bin), args.runs)
