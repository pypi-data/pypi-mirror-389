###############################################################################
# (c) Copyright 2024 CERN for the benefit of the LHCb Collaboration           #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
"""ROOT file operations for skimming and merging."""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections import defaultdict

from ..cli_utils import log_error, log_info, log_warn  # type: ignore
from ..options import Options
from ..utils import (
    get_output_filename,
    read_xml_file_catalog,
    resolve_input_files,
    write_summary_xml,
)


def skim_and_merge(options: Options, *extra_args):
    """Take given input files, merge specified object keys from them and write to a corresponding output file."""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--write",
        action="append",
        help="Write to given file name the tree(s) matching a regular expression . e.g. --write XICP.ROOT='Xic.*/DecayTree'",
    )
    parser.add_argument(
        "--lumi-tuple",
        default="(GetIntegratedLuminosity|lumiTree)",
        help="Regular expression to match key containing Luminosity information. Set to 'none' to ignore.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Allow trees in the input file(s) to be missing from the output files.",
    )
    parser.add_argument(
        "--allow-duplicates",
        action="store_true",
        help="Allow trees in the input file(s) to be copied to more than one output file.",
    )

    extra_opts = parser.parse_args(extra_args)

    if options.n_threads > 1:
        raise NotImplementedError

    import ROOT  # type: ignore

    def clean_directories(filename):
        log_info(f"-- clean up {filename} --")
        rf = ROOT.TFile.Open(filename, "UPDATE")  # pylint: disable=no-member
        for key in rf.GetListOfKeys():
            key_name = key.GetName()
            key_type = key.GetClassName()
            if key_type in ["TDirectory", "TDirectoryFile"]:
                key_object = rf.Get(key_name)
                # check that the tdir is empty
                if key_object.GetNkeys() == 0:
                    rf.rmdir(key_name)
                    log_info(f"{filename}: Cleaned up empty {key_type} {key_name}.")
                else:
                    log_info(
                        f"{filename}: Purging unnecessary cycles in non-empty {key_type} {key_name}."
                    )
                    key_object.Purge()
        rf.Close()

    compression_level = None
    if options.compression:
        # pylint: disable=no-member
        algorithms = {
            "ZLIB": ROOT.RCompressionSetting.EAlgorithm.kZLIB,
            "ZSTD": ROOT.RCompressionSetting.EAlgorithm.kZSTD,
            "LZ4": ROOT.RCompressionSetting.EAlgorithm.kLZ4,
            "LZMA": ROOT.RCompressionSetting.EAlgorithm.kLZMA,
        }
        algo = options.compression.algorithm
        level = options.compression.level
        if algo not in algorithms:
            log_error(f"Unknown compression algorithm {algo}")
            sys.exit(1)
        compression_level = algorithms[algo] * 100 + int(level)
        log_info(f"Compression specified as {algo}:{level} ({compression_level})")

    input_files = options.input_files
    if options.xml_file_catalog:
        file_catalog = read_xml_file_catalog(options.xml_file_catalog)
        input_files = resolve_input_files(options.input_files, file_catalog)

    output_files: set = set()
    all_trees: set = set()
    tree_keys = defaultdict(set)
    lumi_tree_key = None
    for input_file in input_files:
        rf = ROOT.TFile.Open(input_file)  # pylint: disable=no-member
        for key in rf.GetListOfKeys():
            key_name = key.GetName()
            key_type = key.GetClassName()

            # check if TDir is empty and should be ignored
            if key_type in ["TDirectory", "TDirectoryFile"]:
                key_object = rf.Get(key_name)
                # check whether the tdir is empty
                if key_object.GetNkeys() == 0:
                    log_info(
                        f"{input_file}: empty {key_type} {key_name} - not considered."
                    )
                    continue

            if re.match(extra_opts.lumi_tuple, key_name) is None:
                no_match = True
                for out_fn in get_output_filename(key_name, options, extra_opts):
                    no_match = False
                    tree_keys[out_fn].add(key_name)
                if no_match:  # FIXME can we do better?!
                    tree_keys[None].add(key_name)
            else:
                lumi_tree_key = key_name
                for out_fn in get_output_filename(
                    key_name, options, extra_opts, lumi_tree_key=lumi_tree_key
                ):
                    tree_keys[out_fn].add(key_name)
            all_trees.add(key_name)
        rf.Close()
        del rf

    if not lumi_tree_key and extra_opts.lumi_tuple != "none":
        log_info(
            f"Luminosity info directory {extra_opts.lumi_tuple} was not found in any input file."
        )

    # check for duplication
    for tree_name in all_trees:
        if lumi_tree_key == tree_name:
            continue  # duplicates are normal for the lumi trees.
        found = 0
        for trees in tree_keys.values():
            if tree_name in trees:
                found += 1
            if found > 1 and not extra_opts.allow_duplicates:
                log_error(
                    f"Duplicates of directory {tree_name} across more than one file. Set --allow-duplicates if this is intended."
                )
                sys.exit(1)

    for stream, tree_names in tree_keys.items():
        if stream is None:
            for tree_name in tree_names:
                log_warn(f"Tree {tree_name} is missing from output file(s).")
            if extra_opts.allow_missing:
                continue
            log_error(
                "Some directories of the input files would not be copied to any output files. Set --allow-missing if this is intended."
            )
            sys.exit(1)

        op_time = time.time()
        # isLocal, histoOneGo (?)
        merger = ROOT.TFileMerger(False, False)  # pylint: disable=no-member
        merger.SetPrintLevel(2)
        if options.compression:
            merger.SetFastMethod(not options.compression.optimise_baskets)

        for input_file in input_files:
            if not merger.AddFile(input_file):
                log_error(f"Couldn't add input file to merger: {input_file}")
                sys.exit(1)

        merge_opts = (
            ROOT.TFileMerger.kAll  # pylint: disable=no-member
            | ROOT.TFileMerger.kRegular  # pylint: disable=no-member
            | ROOT.TFileMerger.kOnlyListed  # pylint: disable=no-member
        )

        for tree_name in tree_names:
            log_info(
                f"SKIM directory {tree_name} FROM {len(input_files)} files ---> {options.get_output_file(stream)}"
            )
            merger.AddObjectNames(tree_name)

        if compression_level:
            merger.OutputFile(
                options.get_output_file(stream),
                "RECREATE",
                compression_level,
            )
        else:
            merger.OutputFile(options.get_output_file(stream), "RECREATE")
        output_files.add(options.get_output_file(stream))
        if not merger.PartialMerge(merge_opts):
            log_error("TFileMerger::PartialMerge failed!")
            sys.exit(1)

        # Explicitly delete TFileMerger as if not the file is not fully flushed to disk
        # and the later call to clean_directories will corrupt the file
        del merger

        log_info(f"    ... took {time.time() - op_time:.1f} seconds")

    for ofn in output_files:
        clean_directories(ofn)

    write_summary_xml(options, output_files)
    return options
