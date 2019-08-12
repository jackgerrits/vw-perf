# vw-perf

In order to compare performance of [Vowpal Wabbit](https://github.com/VowpalWabbit/vowpal_wabbit) across versions a consistent set of benchmarks should be used, this repo aims to collect these benchmarks and make them easily reproducible. Benchmarks are command line based so they are simple to specify. Also because VW's primary interface is command line and so this is the only way to be able to run a set of benchmarks over many versions.

## Benchmarks
Below is a list of current benchmarks and a brief explanation of what they test.
- `--no_stdin`
  - Simple startup time test
  - Tests the reduction stack setup performance
- `--no_stdin -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -q AB -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t -t`
  - Tests for performance of handling large command lines
- `-d ./data/rcv1/rcv1/rcv1.train.vw.gz -f r_temp`
  - Trains simple GD learner over large dataset (~433mb)
- `-d ./data/rcv1/rcv1/rcv1.test.vw.gz -t -i r_temp`
  - Loads a trained model and runs inference
- `--dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0`
  - Tests performance of JSON parsing and training in CB stack
- `-t --dsjson -d ./data/cb_data/cb_data.dsjson --cb_explore_adf --ignore XA -q UB --epsilon 0.2 -l 0.5 --cb_type mtr --power_t 0`
  - Tests performance of JSON parsing and CB stack but in test only mode

## Usage
1. Run `python3 run.py prepare` to download required datasets
2. Run `run.py clone <sha>` to clone and build the given sha
2. Run `run.py --clone_dir ./clones` to run benchmarks against the downloaded sha. This will output results into `data.json`
