import re
import logging
from argparse import ArgumentParser
from copy import copy
from .jmx_replace import walk_etree, ReplaceBearer, ReplaceCCU, ReplaceDuration
from . import jmx_replace as jr
from . import jmx_mapping as jm
from . import sync
from braceexpand import braceexpand

logging.getLogger().setLevel(logging.INFO)


def main_batch(parser, args, unknown):
    #
    # Determine which arg should be split, expand the braces if any
    #
    delim = args.delimiter
    split_index = []
    for idx, arg in enumerate(unknown):
        if delim in arg:
            split_index.append(idx)
    for idx in split_index:
        unknown[idx] = ','.join(braceexpand(unknown[idx]))

    #
    # Check how many splits are there
    # ensure the number of splits in each arg is the same
    #
    split_lengths = []
    for idx in split_index:
        length = len(unknown[idx].split(delim))
        split_lengths.append(length)
        del length
    assert min(split_lengths) == max(split_lengths),\
        "Invalid batch configuration (number of splits don't match)"

    #
    # Map to commands
    #
    num_splits = min(split_lengths)
    for idx in split_index:
        splits = unknown[idx].split(delim)
        for b_idx, split_value in enumerate(splits):
            batch_unknowns[b_idx][idx] = split_value
    batch_args = [parser.parse_args(args_) for args_ in batch_unknowns]

    #
    # Find the attribute that is different over the batch
    #
    diff_attrs = set()
    for args_i in batch_args:
        for args_j in batch_args:
            for k, v in vars(args_i).items():
                if getattr(args_j, k) != v:
                    diff_attrs.add(k)

    #
    # Format the output name using the diff attributes
    #
    for args_i in batch_args:
        fmt = {k: getattr(args_i, k) for k in diff_attrs}
        args_i.output = args_i.output.format_map(fmt)

    #
    # Finally, dispatch the action
    # Recursion, b*tch!
    #
    for args_i in batch_args:
        dispatch_action(parser, args_i, [])


def dispatch_action(parser, args, unknown):
    if args.action == "replace":
        jr.main(args)
    elif args.action == "run":
        from .jmx_run import main as main_run
        main_run(args)
    elif args.action == "batch":
        main_batch(parser, args, unknown)
    elif args.action == "push":
        sync.main_push(args)
    elif args.action == "pull":
        sync.main_pull(args)
    else:
        raise RuntimeError(
            f"The action `{args.action}` is not implemented, sorry")


def main(args=None):
    parser = ArgumentParser()

    actions = parser.add_subparsers(dest="action", required=True)

    #
    # Replace actions
    #
    replace = actions.add_parser("replace")
    jr.add_args(replace)

    #
    # Batch action
    #
    batch = actions.add_parser("batch")
    batch.add_argument("--delimiter", "-d", default=",")

    #
    # Run action
    #
    run = actions.add_parser("run")
    run.add_argument("--input", "-i", required=True)
    run.add_argument("--output", "-o", required=True)
    run.add_argument("--heap", type=int, help="Heap size (in GBs)")
    run.add_argument("--force", "-f", action="store_true",
                     help="Force overwrite the output files")

    #
    # Sync action
    #
    sync_push = actions.add_parser("push")
    sync_push.add_argument("inputs", nargs='*')
    sync_pull = actions.add_parser("pull")
    sync_pull.add_argument("host")

    args, unknown = parser.parse_known_args(args)
    dispatch_action(parser, args, unknown)


if __name__ == "__main__":
    main()
