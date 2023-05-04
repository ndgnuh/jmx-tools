from os import path, walk, makedirs, curdir
from functools import wraps
import re


def find(d, pattern=None):
    results = []
    for root, _, files in walk(d):
        for file in files:
            if pattern is None:
                results.append(path.join(root, file))
            elif re.match(pattern, file) is not None:
                results.append(path.join(root, file))
    return results


def find_jmx(d):
    return find(d, r".+jmx")


def relative_output(input_file, output_dir):
    rp = path.relpath(input_file, curdir)
    return path.join(output_dir, rp, input_file)


def prepare_write(file):
    d = path.dirname(file)
    if d != "":
        makedirs(d, exist_ok=True)


def mux_input_output(input_file, output_file):
    unsupported_case = RuntimeError(
        f"Unsupported case for {input_file} and {output_file}"
    )
    if path.isfile(input_file):
        #
        # If input file is a file,
        # write to output_file/basename if it's a folder
        # write to output_file if it's a file
        # write to itself if output is None
        #
        if output_file is None:
            return [(input_file, input_file)]
        if path.isdir(output_file):
            bn = path.basename(input_file)
            return [(input_file, path.join(output_file, bn))]
        elif path.isfile(output_file):
            return [(input_file, output_file)]
        else:
            raise unsupported_case
    else:
        #
        # If output file is folder,
        # find all the input files inside
        # if output is None, write inplace
        # if output is folder, write and keep sub folder
        # else unsupported
        #
        input_files = find_jmx(input_file)
        if output_file is None:
            return list(zip(input_files, input_files))
        else:
            assert path.isdir(output_file) or not path.exists(output_file)
            if output_file != "":
                makedirs(output_file, exist_ok=True)
            output_files = [
                path.join(output_file, path.relpath(file, curdir))
                for file in input_files
            ]
            return list(zip(input_files, output_files))


def with_mux(main_fn):
    @wraps(main_fn)
    def main(args):
        inputs = mux_input_output(args.input, args.output)
        for input_file, output_file in inputs:
            main_fn(args, input_file, output_file)

    return main


def postman_walk(items, callback):
    is_request = lambda item: "request" in item
    is_collection = lambda item: "item" in item
    for item in items:
        if is_request(item):
            callback(item)
        elif is_collection(item):
            postman_walk(item, callback)


def postman_all_items(postman_config):
    items = []
    def callback(item):
        items.append(item)
    postman_walk(postman_config['item'], callback)
    return items
