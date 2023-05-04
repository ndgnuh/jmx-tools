import sys
import logging
import json
from os import remove, walk, makedirs
from shutil import rmtree
from copy import copy
from subprocess import run, Popen
from os import path, environ
import pandas as pd

if "JMETER_PATH" not in environ:
    logging.warning(
        "JMETER_PATH environment variable not found, using `jmeter`"
    )
    JMETER_PATH = "jmeter"
else:
    JMETER_PATH = environ["JMETER_PATH"]


def get_log_file(jmx_file):
    base = path.splitext(jmx_file)[0]
    return f"{base}.jtl"


def get_dash_folder(jmx_file):
    basedir = path.dirname(jmx_file)
    base = path.basename(path.splitext(jmx_file)[0])
    return path.join(basedir, f"summary-{base}")


def get_summary_file(jmx_file):
    dash = get_dash_folder(jmx_file)
    return path.join(dash, "statistics.json")


def get_jmeter_cmd(jmx_file, jmeter_path=JMETER_PATH):
    cmd = [
        jmeter_path,
        "-n",  # No GUI
        "-t", jmx_file,
        "-l", get_log_file(jmx_file),  # Jmeter log file
        "-e",  # Generate summary at the end
        "-o", get_dash_folder(jmx_file),
    ]
    return cmd


def main_directory(args):
    #
    # Search for jmx files
    #
    jmx_files = []
    for (root, _, files) in walk(args.input):
        jmx_files.extend([path.join(root, file) for file in files
                          if file.endswith(".jmx")])
    jmx_files = sorted(jmx_files)

    #
    # Map to output files
    #
    output_files = []
    output_root = args.output
    for jmx_file in jmx_files:
        relpath = path.relpath(jmx_file)
        output_file = path.join(output_root, jmx_file.replace(".jmx", ".csv"))
        output_files.append(output_file)

    #
    # Recursion, run the main function again
    # but with different inputs
    #
    for jmx_file, output_file in zip(jmx_files, output_files):
        main(args, jmx_file, output_file)


def main(args, jmx_file=None, output_file=None):
    if jmx_file is None:
        jmx_file = args.input
    if output_file is None:
        output_file = args.output

    #
    # Check if the input is a directory
    # Run in directory mode
    #
    if path.isdir(jmx_file):
        if not path.exists(output_file):
            makedirs(output_file)
        assert path.isdir(
            output_file), "Both input and output must be directory"
        return main_directory(args)

    # Run environment
    run_env = copy(environ)

    # Make sure output directory exists
    output_dir = path.dirname(output_file)
    if output_dir != '':
        makedirs(output_dir, exist_ok=True)

    #
    # Check if we need to set the heap size
    #
    if args.heap is not None:
        heap = args.heap
        max_metaspace_size = int(heap / 4 * 1024)
        run_env["HEAP"] = f"-Xms{heap}g -Xmx{heap}g -XX:MaxMetaspaceSize={max_metaspace_size}m"
        logging.info(f"Setting Java heap: {run_env['HEAP']}")

    #
    # Remove output files if forced
    #
    if args.force:
        try:
            rmtree(get_dash_folder(jmx_file))
        except Exception:
            pass
        try:
            remove(get_log_file(jmx_file))
        except Exception:
            pass

    #
    # Run jmeter
    #
    cmd = get_jmeter_cmd(jmx_file)
    proc = Popen(cmd,
                 stdout=sys.stdout,
                 stderr=sys.stderr,
                 env=run_env)
    proc.communicate()

    #
    # Error check
    #
    if proc.returncode != 0:
        logging.error("Something bad has happened, see the log above.")
        sys.exit(proc.returncode)
        return

    #
    # Generate summary file
    #
    summary_file = get_summary_file(jmx_file)
    with open(summary_file) as f:
        data = json.load(f)
    df = pd.DataFrame(list(data.values()))
    df = df.sort_values(by=["sampleCount", "transaction"])
    df.to_csv(output_file, index=False)
    logging.info(f"Output written to {output_file}")
