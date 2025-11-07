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
"""MDF file utilities."""

from __future__ import annotations

import ctypes
import time
from typing import BinaryIO, cast

from ..options import Options
from ..utils import read_xml_file_catalog, resolve_input_files, write_summary_xml

# Constants
MDF_MERGE_CHUNK_SIZE = 1024 * 1024  # 1MB chunk size for merging MDF files


def _get_mdf_event_size(buffer: ctypes.Array[ctypes.c_char]) -> int:
    """Extract the event size from the MDF buffer."""
    raw_bytes = buffer.raw
    size = int.from_bytes(raw_bytes[0:4], "little")
    for i in range(4, 12, 4):
        if int.from_bytes(raw_bytes[i : i + 4], "little") != size:
            raise ValueError("MDF file does not have a valid header.")
    return size


def merge_mdf(options: Options):
    """Merge MDF files into a single compressed output file."""
    import ROOT  # type: ignore[import-untyped]
    import zstandard

    input_files = options.input_files
    if options.xml_file_catalog:
        file_catalog = read_xml_file_catalog(options.xml_file_catalog)
        input_files = resolve_input_files(options.input_files, file_catalog)

    output_ctx: BinaryIO
    if options.compression is None:
        print("Merging MDF files without compression...")
        output_ctx = open(options.output_file, "wb")
    elif options.compression.algorithm == "ZSTD":
        level = options.compression.level * 2
        print(f"Using Zstandard compressor with level {level}...")
        comp_params = zstandard.ZstdCompressionParameters.from_level(level)
        comp = zstandard.ZstdCompressor(compression_params=comp_params)
        raw_file = open(  # pylint: disable=consider-using-with
            options.output_file, "wb"
        )
        output_ctx = cast(BinaryIO, comp.stream_writer(raw_file))
    else:
        raise NotImplementedError(options.compression)

    bytes_read = 0
    next_progress_print = MDF_MERGE_CHUNK_SIZE * 100
    buffer = ctypes.create_string_buffer(MDF_MERGE_CHUNK_SIZE)
    start_time = time.time()
    with output_ctx as fh:
        for input_file in input_files:
            input_file = input_file.removeprefix("mdf:")
            print("Reading input file:", input_file)
            header_checked = False
            with ROOT.TFile.Open(  # pylint: disable=no-member
                f"{input_file}?filetype=raw"
            ) as rf:
                to_read = rf.GetSize()
                while to_read > 0:
                    requested = min(to_read, MDF_MERGE_CHUNK_SIZE)
                    failure = rf.ReadBuffer(buffer, requested)
                    if failure:
                        raise RuntimeError(f"Failed to read from file {input_file}.")
                    to_read -= requested
                    bytes_read += requested

                    # Safety check to make sure we're actually reading a valid MDF file
                    if not header_checked:
                        first_event_size = _get_mdf_event_size(buffer)
                        # If possible, check the second event header
                        if first_event_size + 12 < bytes_read:
                            second_buffer = ctypes.create_string_buffer(
                                buffer.raw[first_event_size:]
                            )
                            _get_mdf_event_size(second_buffer)
                        header_checked = True

                    if bytes_read >= next_progress_print:
                        print(
                            f"Status: {bytes_read / (1024 * 1024):.2f} MiB read and "
                            f"{fh.tell() / (1024 * 1024):.2f} MiB written "
                            f"in {time.time() - start_time:.2f} seconds."
                        )
                        next_progress_print += MDF_MERGE_CHUNK_SIZE * 100

                    fh.write(memoryview(buffer)[:requested])
        fh.flush()
        bytes_written = fh.tell()
        end_time = time.time()
        print(f"Total bytes read: {bytes_read} ({bytes_read / (1024 * 1024):.2f} MiB)")
        print(
            f"Total bytes written: {bytes_written} ({bytes_written / (1024 * 1024):.2f} MiB)"
        )
        print(f"Compression ratio: {bytes_written / bytes_read:.2f}")
        print(f"Total time taken: {end_time - start_time:.2f} seconds.")

    print(f"Finished merging MDF files into {options.output_file}.")
    write_summary_xml(options, {options.output_file})
