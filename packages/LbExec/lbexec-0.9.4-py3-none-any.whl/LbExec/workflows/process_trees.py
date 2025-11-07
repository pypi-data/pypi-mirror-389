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
"""Decorator functions for workflow automation."""

from __future__ import annotations

import time
from typing import Any, Callable, TypeVar, overload

from ..cli_utils import log_info, log_warn  # type: ignore
from ..options import Options
from ..utils import read_xml_file_catalog, resolve_input_files, write_summary_xml

# Type variables for proper decorator type hints
F = TypeVar("F", bound=Callable[..., Any])


# Type alias for decorated function (takes Options, returns None)
LbExecEntrypoint = Callable[[Options], None]


@overload
def process_trees(
    func: F,
) -> LbExecEntrypoint: ...


@overload
def process_trees(
    func: None = None,
    *,
    pass_all_trees: bool = False,
    branch_regex: str = ".*",
    writable_column_list: list[str] | None = None,
    ignore_lumi_tree: bool = True,
) -> Callable[[F], LbExecEntrypoint]: ...


def process_trees(
    func: F | None = None,
    *,
    pass_all_trees: bool = False,
    branch_regex: str = ".*",
    writable_column_list: list[str] | None = None,
    ignore_lumi_tree: bool = True,
) -> LbExecEntrypoint | Callable[[F], LbExecEntrypoint]:
    """A decorator for processing ROOT trees with automatic discovery and snapshotting.

    This decorator automatically discovers trees in input ROOT files and calls the decorated
    function for each tree (or all trees at once if pass_all_trees=True). The processed
    RDataFrame objects are then automatically saved to the output file.

    Args:
        func: The function to decorate (when used without parentheses)
        pass_all_trees: If True, pass all trees as a dict to the function at once
        branch_regex: Regular expression to select which branches to save (default: ".*")
        writable_column_list: Explicit list of column names to save (mutually exclusive with branch_regex)
        ignore_lumi_tree: If True, skip luminosity trees during processing

    Returns:
        The decorated function that processes trees according to the specified parameters

    Usage Examples:
        # Basic usage with defaults
        @process_trees
        def my_analysis(tree_name, rdf):
            return rdf.Filter("pt > 10")

        # With specific branch selection
        @process_trees(branch_regex="muon_.*")
        def muon_analysis(tree_name, rdf):
            return rdf.Define("muon_eta", "muon_eta * 2")

        # Process all trees using one function
        @process_trees(pass_all_trees=True)
        def multi_tree_analysis(tree_dict):
            # tree_dict is {tree_name: rdf, ...}

            tree_dict["tree1/DecayTree"] = tree_dict["tree1/DecayTree"].Filter("mass > 5000")
            tree_dict["tree2/DecayTree"] = tree_dict["tree2/DecayTree"].Define("new_var", "var1 + var2")

            return tree_dict

        # Explicit column selection
        @process_trees(writable_column_list=["pt", "eta", "phi"])
        def minimal_output(tree_name, rdf):
            return rdf.Filter("pt > 20")

    Raises:
        ValueError: If both writable_column_list and branch_regex are specified
        TypeError: If arguments have incorrect types
        RuntimeError: If ROOT files cannot be opened or are corrupted
    """

    # Validation
    if writable_column_list and branch_regex != ".*":
        raise ValueError("Cannot specify both writable_column_list and branch_regex.")

    if branch_regex and not isinstance(branch_regex, str):
        raise TypeError("branch_regex must be a string")

    if writable_column_list and not isinstance(writable_column_list, list):
        raise TypeError("writable_column_list must be a list of strings")

    def decorator(process_tree_fn: F) -> LbExecEntrypoint:
        def entrypoint(options: Options) -> None:
            import ROOT  # type: ignore[import-untyped]

            start_time = time.time()
            log_info(
                f"Starting tree processing with function: {process_tree_fn.__name__}"
            )

            input_files = options.input_files
            if options.xml_file_catalog:
                file_catalog = read_xml_file_catalog(options.xml_file_catalog)
                input_files = resolve_input_files(options.input_files, file_catalog)

            trees = []

            # Use context-like management for ROOT file
            rf = None
            try:
                rf = ROOT.TFile.Open(input_files[0])  # pylint: disable=no-member
                if not rf or rf.IsZombie():
                    raise RuntimeError(f"Failed to open ROOT file: {input_files[0]}")

                def _discover_trees_in_file(root_file):
                    """Helper function to discover trees in a ROOT file."""
                    discovered_trees = []
                    for key in root_file.GetListOfKeys():
                        key_name = key.GetName()
                        classname = key.GetClassName()
                        log_info(f"Found object {key_name}: {classname}")

                        if classname == "TTree":
                            discovered_trees.append(key_name)
                        elif classname.startswith("TDirectory"):
                            subdir = root_file.Get(key_name)
                            if not subdir:
                                continue
                            for key2 in subdir.GetListOfKeys():
                                if key2.GetClassName() == "TTree":
                                    discovered_trees.append(
                                        f"{key_name}/{key2.GetName()}"
                                    )
                    return discovered_trees

                trees = _discover_trees_in_file(rf)

                log_info(f"Found {len(trees)} trees in input files: {trees}")
            finally:
                if rf:
                    rf.Close()
                    del rf

            if not trees:
                log_warn("No trees found in input files")
                write_summary_xml(options, {options.output_file})
                return

            tree_name_to_rdf = {}

            for tree_name in trees:
                rdf = ROOT.RDataFrame(  # pylint: disable=no-member
                    tree_name,
                    input_files,
                )

                if (
                    tree_name not in ["lumiTree", "GetIntegratedLuminosity/LumiTuple"]
                    or not ignore_lumi_tree
                ):
                    tree_name_to_rdf[tree_name] = rdf

            tree_name_keys = list(tree_name_to_rdf.keys())

            if not pass_all_trees:
                for tree_name in tree_name_keys:
                    out_opts = ROOT.RDF.RSnapshotOptions()  # pylint: disable=no-member
                    out_opts.fMode = (
                        "UPDATE"  # In case the Tree name maps to the same file
                    )
                    out_opts.fOverwriteIfExists = True
                    log_info(f"Loading tree: {tree_name}")
                    rdf = process_tree_fn(tree_name, tree_name_to_rdf[tree_name])

                    rdf.Snapshot(
                        tree_name,
                        options.output_file,
                        writable_column_list or branch_regex,
                        out_opts,
                    )
                    log_info(
                        f"Snapshot of {tree_name} written to {options.output_file}"
                    )
                    del rdf
            else:
                log_info(f"Processing all trees: {tree_name_keys!r}")
                tree_name_to_rdf = process_tree_fn(tree_name_to_rdf)
                for tree_name in tree_name_keys:
                    out_opts = ROOT.RDF.RSnapshotOptions()  # pylint: disable=no-member
                    out_opts.fMode = (
                        "UPDATE"  # In case the Tree name maps to the same file
                    )
                    out_opts.fOverwriteIfExists = True

                    tree_name_to_rdf[tree_name].Snapshot(
                        tree_name,
                        options.output_file,
                        writable_column_list or branch_regex,
                        out_opts,
                    )
                    log_info(
                        f"Snapshot of {tree_name} written to {options.output_file}"
                    )

            write_summary_xml(
                options,
                {options.output_file},
            )

            end_time = time.time()
            log_info(
                f"Tree processing completed in {end_time - start_time:.2f} seconds"
            )

        return entrypoint

    # Handle both @process_trees and @process_trees() usage
    if func is None:
        # Called with parentheses: @process_trees() or @process_trees(args)
        return decorator
    # Called without parentheses: @process_trees
    return decorator(func)
