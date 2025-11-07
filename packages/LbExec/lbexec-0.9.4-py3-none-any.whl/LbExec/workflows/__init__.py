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
"""Workflows package for LbExec.

This package contains various workflow functions for processing ROOT files,
including skimming and merging operations, MDF file processing, and the
process_trees decorator for automated tree processing.
"""

from .mdf_utils import merge_mdf
from .process_trees import process_trees
from .skim_and_merge import skim_and_merge

__all__ = [
    "process_trees",
    "skim_and_merge",
    "merge_mdf",
]
