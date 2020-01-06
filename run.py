import os
import time
import argparse
import subprocess
import util
import find
import clone
import json
import textwrap
import sys

import prepare
import benchmark
import find
import data
from pathlib import Path

from typing import Callable, Tuple, List, Union, TextIO, Optional, Any, Dict


def boolean_string(bool_str: str) -> bool:
    bool_str = bool_str.lower()
    if bool_str not in {'false', 'true'}:
        raise ValueError('Not a valid boolean string')
    return bool_str == 'true'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "run.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
      subcommands:
        run\t\tMain perf testing harness
        prepare\tDownloads and extracts required datasets for perf harness, and sets up cache
        clone\t\tUtility to clone and build commits in expected directory structure
        find\t\tUsed to find binaries in a directory (not important)

      Use `<subcommand> -h` to see usage of a subcommand
      '''))
    subparsers = parser.add_subparsers(dest='command')
    parser.add_argument('--cache_dir',
                           type=str,
                           help='Choose the cache directory, defaults to ~/.vw_benchmark_cache',
                           default=None)

    run_parser = subparsers.add_parser("run")
    clone_parser = subparsers.add_parser("clone")
    prepare_parser = subparsers.add_parser("prepare")
    find_parser = subparsers.add_parser("find")
    data_parser = subparsers.add_parser("merge")

    run_group = run_parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument('--binary',
                           type=str,
                           help='Test a specific binary',
                           default=None)
    run_parser.add_argument('--reference_binary',
                           type=str,
                           help='Binary to use a reference',
                           default=None)
    run_group.add_argument('--commits',
                           type=str,
                           nargs='+',
                           help='List of all commits to test',
                           default=None)
    run_group.add_argument('--num',
                           type=int,
                           help='Number of master commits into past to test',
                           default=None)
    run_group.add_argument('--from',
                           type=str,
                           help='Ref to use a from in range',
                           default=None)
    run_group.add_argument('--to',
                           type=str,
                           help='Ref to use as to in range',
                           default=None)
    run_parser.add_argument("--runs",
                            help="How many runs to average over",
                            default=1,
                            type=int)
    run_parser.add_argument("--skip_existing",
                            help="Skip over commits already done",
                            default=True,
                            type=boolean_string)

    clone_group = clone_parser.add_mutually_exclusive_group(required=True)
    clone_group.add_argument('--commits',
                             type=str,
                             nargs='+',
                             help='List of all commits to checkout',
                             default=None)
    clone_group.add_argument(
        '--num',
        type=int,
        help='Number of master commits into past to checkout',
        default=None)
    clone_group.add_argument('--from',
                             type=str,
                             help='Ref to use a from in range',
                             dest='from_ref',
                             default=None)
    clone_group.add_argument('--to',
                             type=str,
                             help='Ref to use as to in range',
                             dest='to_ref',
                             default=None)

    find_parser.add_argument("--name", help="Binary name to find")
    find_parser.add_argument("--path",
                             help="Path to find in",
                             default="./clones/")

    data_parser.add_argument("--files",
                             help="Data files to merge",
                             type=str,
                             nargs='+',
                             default=[],
                             required=True)
    data_parser.add_argument("--merged_name",
                             help="Name of merged file",
                             type=str,
                             default="merged.json")

    args = parser.parse_args()
    
    if args.cache_dir is None:
        args.cache_dir = os.path.join(Path.home(), ".vw_benchmark_cache")

    # Check if a command was supplied
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    elif args.command == "clone":
        clone.run(args.commits, args.num, args.from_ref, args.to_ref, args.cache_dir)
    elif args.command == "prepare":
        prepare.run(args.cache_dir)
    elif args.command == "run":
        if args.binary is None:
            benchmark.run(args.commits, args.num, args.from_ref, args.to_ref,
                        args.runs, args.skip_existing, args.cache_dir)
        else:
            benchmark.run_for_binary(args.binary, args.reference_binary, args.runs, args.cache_dir)
    elif args.command == "find":
        find.run(args.bin_name, args.path)
    elif args.command == "merge":
        data.merge(args.files, args.merged_name)
