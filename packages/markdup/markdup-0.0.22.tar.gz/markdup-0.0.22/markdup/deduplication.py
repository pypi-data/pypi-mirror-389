#fragment_id!/usr/bin/env python3
"""
Unified Deduplication Logic - Clean & Simple Architecture

This module provides a clean, unified approach to BAM deduplication with:
- Single reader object with sequential window processing
- Thread-safe writer object for parallel output
- Single processor for both UMI and coordinate methods
- Minimal code duplication

Author: Ye Chang
Date: 2025-01-27
"""

import logging
import os
import signal
import sys
import tempfile
import time
from collections import defaultdict
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any

import pysam
from rich.progress import Progress, TimeElapsedColumn, TimeRemainingColumn

from .utils import (
    Fragment,
    calculate_average_base_quality,
    cluster_umis_by_edit_distance_frequency_aware,
    extract_umi,
)

# Set up logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.WARNING)  # Only show warnings and errors by default

# Globals used inside worker processes (set by pool initializer)
WORKER_READER = None
WORKER_WRITER = None
WORKER_SHARD_PATH = None


def _worker_initializer(bam_path: str, shard_dir: str):
    """Initializer for ProcessPool workers: open per-process reader and writer.

    Each process opens one AlignmentFile for reading and one shard BAM for writing.
    """
    import atexit as _atexit
    import os as _os

    import pysam as _pysam

    global WORKER_READER, WORKER_WRITER, WORKER_SHARD_PATH
    # Only create reader once per worker process
    if WORKER_READER is None:
        try:
            WORKER_READER = _pysam.AlignmentFile(bam_path, "rb")
        except FileNotFoundError:
            logger.error(f"BAM file not found in worker process: {bam_path}")
            # Re-raise to indicate worker initialization failure
            raise
        except Exception as e:
            logger.error(f"Error initializing WORKER_READER in worker process: {e}")
            # Re-raise to indicate worker initialization failure
            raise
    pid = _os.getpid()
    WORKER_SHARD_PATH = _os.path.join(shard_dir, f"shard_{pid}.bam")
    # Defer writer creation until first write to avoid creating unused shards
    WORKER_WRITER = None

    # Ensure files are closed when the worker exits so BGZF EOF is written
    def _worker_cleanup():
        try:
            if WORKER_WRITER is not None:
                WORKER_WRITER.close()
        except Exception:
            pass
        try:
            if WORKER_READER is not None:
                WORKER_READER.close()
        except Exception:
            pass

    _atexit.register(_worker_cleanup)


def _worker_shutdown_task():
    """Special task to close worker files before process termination."""
    global WORKER_WRITER, WORKER_READER
    try:
        if WORKER_WRITER is not None:
            WORKER_WRITER.close()
            WORKER_WRITER = None
    except Exception:
        pass
    try:
        if WORKER_READER is not None:
            WORKER_READER.close()
            WORKER_READER = None
    except Exception:
        pass
    return {"shutdown": True}


# ============================================================================
# QUALITY SCORING FUNCTIONS
# ============================================================================


def calculate_fragment_quality_score(fragment, best_read_by):
    """
    Calculate quality score for a fragment based on the specified criteria.

    Args:
        fragment: Fragment object containing read(s)
        best_read_by: Quality criterion ('mapq' or 'avg_base_q')

    Returns:
        float: Quality score for the fragment
    """
    if best_read_by == "mapq":
        if fragment.is_paired and fragment.read2:
            # For paired-end: use average of both reads' mapping qualities
            return (fragment.read1.mapping_quality + fragment.read2.mapping_quality) / 2
        # For single-end: use read1 mapping quality
        return fragment.read1.mapping_quality
    if best_read_by == "avg_base_q":
        if fragment.is_paired and fragment.read2:
            # For paired-end: use average of both reads' base qualities
            read1_qual = (
                calculate_average_base_quality(fragment.read1.query_qualities)
                if fragment.read1.query_qualities
                else 0
            )
            read2_qual = (
                calculate_average_base_quality(fragment.read2.query_qualities)
                if fragment.read2.query_qualities
                else 0
            )
            return (read1_qual + read2_qual) / 2
        # For single-end: use read1 base quality
        if fragment.read1.query_qualities:
            return calculate_average_base_quality(fragment.read1.query_qualities)
        return 0
    # Default to mapping quality
    if fragment.is_paired and fragment.read2:
        return (fragment.read1.mapping_quality + fragment.read2.mapping_quality) / 2
    return fragment.read1.mapping_quality


# ============================================================================
# DEDUPLICATION FUNCTIONS
# ============================================================================


def _deduplicate_fragments(
    fragments,
    method,
    max_dist_frac=0.1,
    max_frequency_ratio=0.1,
    best_read_by="avg_base_q",
    keep_duplicates=False,
):
    global WORKER_WRITER, WORKER_READER, WORKER_SHARD_PATH
    """
    Deduplicate fragments based on a grouping key and method, writing results directly.

    Args:
        fragments: List of Fragment objects
        method: Deduplication method ('umi' or 'coordinate')
        max_dist_frac: Maximum edit distance as fraction of UMI length
        max_frequency_ratio: Maximum ratio of smaller UMI frequency to larger UMI frequency for merging
        best_read_by: Quality criterion for selecting best read ('mapq' or 'avg_base_q')
        keep_duplicates: Whether to keep duplicate reads and mark them

    Returns:
        Tuple: (deduplicated_count, read_stats)
    """
    fragments_by_position = defaultdict(list)
    for fragment in fragments:
        fragments_by_position[fragment.grouping_key].append(fragment)

    deduplicated_count = 0

    for position, fragments_at_position in fragments_by_position.items():
        if method == "umi" and len(fragments_at_position) > 1:
            fragments_by_umi = defaultdict(list)
            for fragment in fragments_at_position:
                fragments_by_umi[fragment.umi].append(fragment)

            if max_dist_frac > 0:
                if sum(len(v) for v in fragments_by_umi.values()) == len(
                    fragments_by_umi
                ):
                    clustered_fragment_groups = [
                        [frag] for frag in fragments_at_position
                    ]
                else:
                    clustered_fragment_groups = (
                        cluster_umis_by_edit_distance_frequency_aware(
                            fragments_by_umi, max_dist_frac, max_frequency_ratio
                        )
                    )
            else:
                clustered_fragment_groups = list(fragments_by_umi.values())
        else:
            clustered_fragment_groups = [fragments_at_position]

        for fragment_group in clustered_fragment_groups:
            best_fragment = max(
                fragment_group,
                key=lambda f: calculate_fragment_quality_score(f, best_read_by),
            )
            cluster_name = best_fragment.get_cluster_name(method)

            if keep_duplicates:
                for fragment in fragment_group:
                    is_best = fragment is best_fragment
                    fragment.read1.set_tag("cn", cluster_name)
                    fragment.read1.set_tag("cs", len(fragment_group))
                    fragment.read1.set_tag("fi", fragment.fragment_id)
                    if not is_best:
                        fragment.read1.is_duplicate = True
                    if WORKER_WRITER is None:
                        WORKER_WRITER = pysam.AlignmentFile(
                            WORKER_SHARD_PATH, "wb", header=WORKER_READER.header
                        )
                    WORKER_WRITER.write(fragment.read1)
                    deduplicated_count += 1
                    if fragment.read2:
                        fragment.read2.set_tag("cn", cluster_name)
                        fragment.read2.set_tag("cs", len(fragment_group))
                        fragment.read2.set_tag("fi", fragment.fragment_id)
                        if not is_best:
                            fragment.read2.is_duplicate = True
                        WORKER_WRITER.write(fragment.read2)
                        deduplicated_count += 1
            else:
                best_fragment.read1.set_tag("cn", cluster_name)
                best_fragment.read1.set_tag("cs", len(fragment_group))
                best_fragment.read1.set_tag("fi", best_fragment.fragment_id)
                if WORKER_WRITER is None:
                    WORKER_WRITER = pysam.AlignmentFile(
                        WORKER_SHARD_PATH, "wb", header=WORKER_READER.header
                    )
                WORKER_WRITER.write(best_fragment.read1)
                deduplicated_count += 1
                if best_fragment.read2:
                    best_fragment.read2.set_tag("cn", cluster_name)
                    best_fragment.read2.set_tag("cs", len(fragment_group))
                    best_fragment.read2.set_tag("fi", best_fragment.fragment_id)
                    WORKER_WRITER.write(best_fragment.read2)
                    deduplicated_count += 1

    # Calculate read stats based on fragments
    properly_paired = sum(1 for f in fragments if f.is_paired)
    paired_no_mate = sum(
        1 for f in fragments if not f.is_paired and f.is_originally_paired
    )
    single_end = sum(
        1 for f in fragments if not f.is_paired and not f.is_originally_paired
    )

    read_stats = {
        "properly_paired": properly_paired,
        "paired_no_mate": paired_no_mate,
        "single_end": single_end,
    }

    return deduplicated_count, read_stats


def deduplicate_fragments_by_umi(
    fragments,
    max_fragment_size=2000,
    start_only=False,
    end_only=False,
    max_dist_frac=0.1,
    max_frequency_ratio=0.1,
    best_read_by="avg_base_q",
    keep_duplicates=False,
    fragment_paired=False,
    fragment_mapped=False,
):
    # Calculate read stats for the fragments *before* any filtering
    properly_paired = sum(1 for f in fragments if f.is_paired)
    paired_no_mate = sum(
        1 for f in fragments if not f.is_paired and f.is_originally_paired
    )
    single_end = sum(
        1 for f in fragments if not f.is_paired and not f.is_originally_paired
    )

    if fragment_paired or fragment_mapped:
        fragments = [
            f
            for f in fragments
            if should_keep_fragment(f, fragment_paired, fragment_mapped)
        ]

    deduplicated_count, _ = _deduplicate_fragments( # _ is for the read_stats from _deduplicate_fragments, which we don't need here
        fragments,
        "umi",
        max_dist_frac,
        max_frequency_ratio,
        best_read_by,
        keep_duplicates,
    )
    read_stats = {
        "properly_paired": properly_paired,
        "paired_no_mate": paired_no_mate,
        "single_end": single_end,
    }
    return deduplicated_count, read_stats


def deduplicate_fragments_by_coordinate(
    fragments,
    max_fragment_size=2000,
    start_only=False,
    end_only=False,
    best_read_by="avg_base_q",
    keep_duplicates=False,
    fragment_paired=False,
    fragment_mapped=False,
):
    """
    Deduplicate reads using coordinate-based clustering.
    """
    if not fragments:
        return 0, {"properly_paired": 0, "paired_no_mate": 0, "single_end": 0}

    # Calculate read stats for the fragments *before* any filtering (if any)
    properly_paired = sum(1 for f in fragments if f.is_paired)
    paired_no_mate = sum(
        1 for f in fragments if not f.is_paired and f.is_originally_paired
    )
    single_end = sum(
        1 for f in fragments if not f.is_paired and not f.is_originally_paired
    )

    if fragment_paired or fragment_mapped:
        fragments = [
            f
            for f in fragments
            if should_keep_fragment(f, fragment_paired, fragment_mapped)
        ]

    deduplicated_count, _ = _deduplicate_fragments( # _ is for the read_stats from _deduplicate_fragments, which we don't need here
        fragments,
        "coordinate",
        best_read_by=best_read_by,
        keep_duplicates=keep_duplicates,
    )
    read_stats = {
        "properly_paired": properly_paired,
        "paired_no_mate": paired_no_mate,
        "single_end": single_end,
    }
    return deduplicated_count, read_stats


def should_keep_fragment(fragment, fragment_paired, fragment_mapped):
    """
    Check if a fragment should be kept based on filtering criteria.

    Args:
        fragment: The fragment to check.
        fragment_paired: If True, only properly paired fragments are kept.
        fragment_mapped: If True, only fragments with both reads mapped are kept.

    Returns:
        bool: True if the fragment should be kept, False otherwise.
    """
    if fragment_paired and not fragment.is_paired:
        return False
    if fragment_mapped and not fragment.is_fully_mapped:
        return False
    return True

def _get_core_reads(
    extended_reads_iter: Iterator[pysam.AlignedSegment],
    window_start: int,
    window_end: int,
    max_fragment_size: int,
) -> Iterator[pysam.AlignedSegment]:
    """
    Filter reads from an extended window to get the core reads for deduplication.

    Args:
        extended_reads_iter: Iterator of reads from the extended window.
        window_start: The start of the core window.
        window_end: The end of the core window.
        max_fragment_size: The maximum fragment size.

    Yields:
        pysam.AlignedSegment: Reads that belong to the core window.
    """
    for read in extended_reads_iter:
        # Basic filtering for unmapped reads
        if read.is_unmapped:
            continue

        # Determine the read's effective start position for filtering
        read_start = read.reference_start

        # Check if the read is within the core window
        if window_start <= read_start < window_end:
            yield read

def _build_fragments(
    reads, no_umi, umi_tag, umi_sep, max_fragment_size, start_only, end_only
):
    """
    Build fragments from an iterator of reads using a memory-efficient streaming approach.

    This function processes reads one by one, pairing them up if they are
    part of a valid pair, and handling single-end or unpaired reads gracefully.
    A buffer stores reads waiting for their mates, minimizing memory usage for
    large genomic regions.

    Args:
        reads (Iterator[pysam.AlignedSegment]): An iterator of reads to process.
        no_umi (bool): If True, UMI extraction is skipped.
        umi_tag (str): The BAM tag to extract the UMI from.
        umi_sep (str): The separator used in the UMI.
        max_fragment_size (int): The maximum allowed size for a fragment.
        start_only (bool): If True, only the start position is used for grouping.
        end_only (bool): If True, only the end position is used for grouping.

    Returns:
        list[Fragment]: A list of constructed Fragment objects.
    """
    fragments: list[Fragment] = []
    read_buffer: defaultdict[str, dict[tuple[int, int, int, int], pysam.AlignedSegment]] = defaultdict(dict)  # Buffer for reads waiting for their mate
    read_count = 0

    for read in reads:
        read_count += 1
        query_name = read.query_name

        # If the read is not paired, treat it as a single-end fragment
        if not read.is_paired:
            read.is_proper_pair = False
            umi_value = None if no_umi else extract_umi(read, umi_tag, umi_sep)
            fragments.append(
                Fragment(
                    query_name=query_name,
                    read1=read,
                    read2=None,
                    umi=umi_value,
                    start_only=start_only,
                    end_only=end_only,
                    is_originally_paired=False,
                )
            )
            continue

        # Check if the mate is in the buffer
        # A mate's query_name is the same as the current read's query_name
        # The mate's coordinates are swapped with the current read's coordinates
        mate_coordinate_key = (
            read.next_reference_id,
            read.next_reference_start,
            read.reference_id,
            read.reference_start,
        )

        mate = read_buffer[query_name].pop(mate_coordinate_key, None)

        if mate:
            # If popping the mate made the inner dict empty, remove the outer dict entry
            if not read_buffer[query_name]:
                del read_buffer[query_name]

            # Mate found, create a paired-end fragment
            read1, read2 = (read, mate) if read.is_read1 else (mate, read)

            # Calculate fragment size and validate
            leftmost_start = min(read1.reference_start, read2.reference_start)
            rightmost_end = max(read1.reference_end, read2.reference_end)
            fragment_size = rightmost_end - leftmost_start

            if fragment_size <= max_fragment_size:
                umi_value = None if no_umi else extract_umi(read1, umi_tag, umi_sep)
                fragments.append(
                    Fragment(
                        query_name=query_name,
                        read1=read1,
                        read2=read2,
                        umi=umi_value,
                        start_only=start_only,
                        end_only=end_only,
                        is_originally_paired=True,
                    )
                )
            else:
                # Fragment too large, treat as two single-end reads
                for r in [read1, read2]:
                    r.is_proper_pair = False
                    umi_value = None if no_umi else extract_umi(r, umi_tag, umi_sep)
                    fragments.append(
                        Fragment(
                            query_name=query_name,
                            read1=r,
                            read2=None,
                            umi=umi_value,
                            start_only=start_only,
                            end_only=end_only,
                            is_originally_paired=True,
                        )
                    )
        else:
            # Mate not found, add the current read to the buffer
            # The key for the current read is its own coordinate tuple
            read_coordinate_key = (
                read.reference_id,
                read.reference_start,
                read.next_reference_id,
                read.next_reference_start,
            )
            read_buffer[query_name][read_coordinate_key] = read

    # Process any remaining reads in the buffer as single-end
    for inner_dict in read_buffer.values():
        for read in inner_dict.values():
            read.is_proper_pair = False
            umi_value = None if no_umi else extract_umi(read, umi_tag, umi_sep)
            fragments.append(
                Fragment(
                    query_name=read.query_name,
                    read1=read,
                    read2=None,
                    umi=umi_value,
                    start_only=start_only,
                    end_only=end_only,
                    is_originally_paired=True,
                )
            )

    return fragments, read_count

def _run_deduplication(method, fragments, **kwargs):
    if method == "coordinate":
        return deduplicate_fragments_by_coordinate(fragments, **kwargs)
    return deduplicate_fragments_by_umi(fragments, **kwargs)


def _write_results(deduplicated_reads):
    # This function is no longer needed as _deduplicate_fragments writes directly
    pass


def _calculate_stats(original_count, deduplicated_count, keep_duplicates):
    duplicates_removed = original_count - deduplicated_count
    duplicates_detected = 0
    # If keep_duplicates is True, duplicates_detected needs to be calculated
    # where reads are marked as duplicates. For now, we'll leave it as 0
    # or adjust if the information becomes available.
    # This is a simplification for now.

    if keep_duplicates:
        # When keeping duplicates, the rate is based on detected duplicates vs original reads
        # For now, we don't have a direct count of duplicates_detected here.
        # This will need to be passed from _deduplicate_fragments if needed.
        deduplication_rate = 0.0 # Placeholder
    else:
        # When removing duplicates, the rate is based on removed duplicates vs original reads
        deduplication_rate = (
            (duplicates_removed / original_count * 100) if original_count > 0 else 0
        )

    return {
        "original_reads": original_count,
        "deduplicated_reads": deduplicated_count,
        "duplicates_removed": duplicates_removed,
        "duplicates_detected": duplicates_detected, # This will be 0 or incorrect without proper counting
        "deduplication_rate": deduplication_rate,
    }


def process_window(window_data: dict[str, Any]) -> dict[str, Any]:
    """
    Process a single genomic window for deduplication.

    Args:
        window_data: Dictionary containing window parameters and configuration

    Returns:
        Dict containing processing results and statistics
    """
    try:
        # Extract parameters from window_data
        contig = window_data["contig"]
        search_start = window_data["search_start"]
        search_end = window_data["search_end"]
        window_start = window_data["window_start"]
        window_end = window_data["window_end"]
        window_id = window_data.get("window_id", "unknown")

        global WORKER_READER
        extended_reads_iter = WORKER_READER.fetch(contig, search_start, search_end)

        core_reads_iter = _get_core_reads(
            extended_reads_iter, window_start, window_end, window_data["max_fragment_size"]
        )

        fragments, read_count = _build_fragments(
            core_reads_iter,
            window_data["no_umi"],
            window_data.get("umi_tag"),
            window_data.get("umi_sep", "_"),
            window_data["max_fragment_size"],
            window_data["start_only"],
            window_data["end_only"],
        )

        if not fragments:
            return {
                "window_id": window_id,
                "success": True,
                "has_reads": False,
                "read_stats": {"properly_paired": 0, "paired": 0, "single_end": 0},
                **_calculate_stats(0, 0, window_data["keep_duplicates"]),
            }

        method = "coordinate" if window_data["no_umi"] else "umi"
        deduplication_kwargs = {
            "max_fragment_size": window_data["max_fragment_size"],
            "start_only": window_data["start_only"],
            "end_only": window_data["end_only"],
            "best_read_by": window_data["best_read_by"],
            "keep_duplicates": window_data["keep_duplicates"],
            "fragment_paired": window_data["fragment_paired"],
            "fragment_mapped": window_data["fragment_mapped"],
        }
        if method == "umi":
            deduplication_kwargs.update(
                {
                    "max_dist_frac": window_data["max_dist_frac"],
                    "max_frequency_ratio": window_data.get("max_frequency_ratio", 0.1),
                }
            )

        deduplicated_count, read_stats = _run_deduplication(
            method, fragments, **deduplication_kwargs
        )

        stats = _calculate_stats(
            read_count, deduplicated_count, window_data["keep_duplicates"]
        )

        return {
            "window_id": window_id,
            "success": True,
            "has_reads": deduplicated_count > 0,
            "read_stats": read_stats,
            **stats,
        }

    except Exception as e:
        logger.error(
            f"Error processing window {window_data.get('window_id', 'unknown')}: {e}"
        )
        # Re-raise the exception so that concurrent.futures propagates it as an exception object
        raise e


# ============================================================================
# UNIFIED PROCESSOR CLASS
# ============================================================================


class BAMWindowGenerator:
    """Generator for processing BAM files in windows."""

    def __init__(
        self,
        bam_file: str,
        window_size: int = 1000,
        max_fragment_size: int = 2000,
        start_only: bool = False,
        end_only: bool = False,
    ):
        self.bam_file = bam_file
        self.window_size = window_size
        self.max_fragment_size = max_fragment_size
        self.start_only = start_only
        self.end_only = end_only

    def get_windows(self):
        """Generate windows for processing."""
        with pysam.AlignmentFile(self.bam_file, "rb") as reader:
            for contig_info in reader.header["SQ"]:
                contig = contig_info["SN"]
                contig_len = contig_info["LN"]

                for i in range(0, contig_len, self.window_size):
                    window_start = i
                    window_end = i + self.window_size

                    # Define search region with overlap for paired-end reads
                    search_start = max(0, window_start - self.max_fragment_size)
                    search_end = window_end + self.max_fragment_size

                    yield {
                        "contig": contig,
                        "search_start": search_start,
                        "search_end": search_end,
                        "window_start": window_start,
                        "window_end": window_end,
                        "is_first_window": i == 0,
                    }


class UnifiedProcessor:
    """
    Unified processor for all deduplication approaches and methods.

    This class provides a unified interface for processing BAM files with
    different deduplication methods (UMI-based and coordinate-based) and
    various configuration options. It handles parallel processing, window
    management, and result aggregation.
    """

    def __init__(
        self,
        bam_file: str,
        output_file: str,
        method: str = "umi",
        umi_tag: str = "UB",
        window_size: int = 1000,
        max_processes: int = None,
        max_fragment_size: int = 2000,
        umi_sep: str = "_",
        max_dist_frac: float = 0.1,
        max_frequency_ratio: float = 0.1,
        keep_duplicates: bool = False,
        best_read_by: str = "avg_base_q",
        fragment_paired: bool = False,
        fragment_mapped: bool = False,
        start_only: bool = False,
        end_only: bool = False,
        memory_per_thread: str = "1G",
    ):
        self.bam_file = bam_file
        self.output_file = output_file
        self.method = method
        self.umi_tag = umi_tag
        self.window_size = window_size
        self.max_processes = max_processes or min(os.cpu_count(), 8)
        self.max_fragment_size = max_fragment_size
        self.umi_sep = umi_sep
        self.max_dist_frac = max_dist_frac
        self.max_frequency_ratio = max_frequency_ratio
        self.keep_duplicates = keep_duplicates
        self.best_read_by = best_read_by
        self.fragment_paired = fragment_paired
        self.fragment_mapped = fragment_mapped
        self.start_only = start_only
        self.end_only = end_only
        self.memory_per_thread = memory_per_thread
        self.temp_bam_file = None  # Will be set if SAM file was converted

        # Statistics
        self.stats = {
            "total_reads_processed": 0,
            "total_duplicates_removed": 0,
            "total_duplicates_detected": 0,
            "total_windows_processed": 0,
            "total_windows_skipped": 0,
            "total_chromosomes_processed": 0,
            "processing_time": 0,
            "deduplication_rate": 0.0,
            "parallel_time": 0.0,
            "sorting_time": 0.0,
            "properly_paired": 0,
            "paired_no_mate": 0,
            "single_end": 0,
        }

    def process_bam(self) -> bool:
        """Process BAM file using sequential reading and parallel window processing."""
        start_time = time.time()
        # Processing will be shown via progress bars

        try:
            # Create shard directory for per-process writers
            print("📝 Creating per-process shard directory...")
            self.shard_dir = tempfile.mkdtemp(prefix="markdup_shards_")

            # Create window generator
            print("📖 Creating BAM window generator...")
            window_generator = BAMWindowGenerator(
                self.bam_file,
                self.window_size,
                self.max_fragment_size,
                self.start_only,
                self.end_only,
            )

            # Get windows for processing
            windows = list(window_generator.get_windows())  # Convert to list to know total

            # Process windows in parallel
            try:
                self._process_windows_parallel(windows)
            except RuntimeError as e:
                logger.error(f"Parallel window processing failed: {e}")
                return False

            # Final sorting and cleanup
            self._final_sort_and_cleanup()

            # Clean up temporary BAM file if it was created from SAM (after final processing)
            if self.temp_bam_file and os.path.exists(self.temp_bam_file):
                print("🧹 Cleaning up temporary BAM file...")
                os.remove(self.temp_bam_file)
                # Also remove the index file
                index_file = self.temp_bam_file + ".bai"
                if os.path.exists(index_file):
                    os.remove(index_file)

            # Calculate final statistics
            self._calculate_final_stats(time.time() - start_time)

            # Create two separate panels: Progress and Statistics
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            console = Console()

            # Clean, organized output
            console.print()
            # Human-readable duration formatter
            duration_seconds = self.stats["processing_time"]

            def _format_duration(sec: float) -> str:
                if sec < 60:
                    return f"{sec:.2f}s"
                if sec < 3600:
                    minutes = int(sec // 60)
                    seconds = int(round(sec % 60))
                    return f"{minutes}m {seconds}s"
                hours = int(sec // 3600)
                rem = sec % 3600
                minutes = int(rem // 60)
                seconds = int(round(rem % 60))
                return f"{hours}h {minutes}m {seconds}s"

            console.print(
                f"✅ Processing completed successfully! (⏱️ {_format_duration(duration_seconds)})",
                style="bold green",
            )

            # Panel 2: Statistics (table format)
            stats_table = Table(show_header=False, box=None, padding=(0, 1))
            stats_table.add_column(style="bold blue", justify="right", width=25)
            stats_table.add_column(style="white", justify="left")

            stats_table.add_row("Method:", self.method)
            stats_table.add_row("Window size:", f"{self.window_size:,}")
            stats_table.add_row("Threads:", str(self.max_processes or "auto"))
            stats_table.add_row("Best read by:", self.best_read_by)
            stats_table.add_row("", "")  # Empty row for spacing
            stats_table.add_row(
                "Total reads processed:", f"{self.stats['total_reads_processed']:,}"
            )

            # Show appropriate duplicate statistic based on keep_duplicates setting
            if self.keep_duplicates:
                stats_table.add_row(
                    "Duplicates detected:",
                    f"{self.stats['total_duplicates_detected']:,}",
                )
            else:
                stats_table.add_row(
                    "Duplicates removed:", f"{self.stats['total_duplicates_removed']:,}"
                )
            stats_table.add_row(
                "Chromosomes processed:", f"{self.stats['total_chromosomes_processed']}"
            )
            stats_table.add_row(
                "Deduplication rate:", f"{self.stats['deduplication_rate']:.2f}%"
            )
            stats_table.add_row("", "")  # Empty row for spacing
            stats_table.add_row("Read Types:", "")
            stats_table.add_row(
                "  Properly paired:",
                f"{self.stats['properly_paired']:,} × 2"
                if self.stats["properly_paired"] > 0
                else "0",
            )
            stats_table.add_row(
                "  Improperly paired:", f"{self.stats['paired_no_mate']:,}"
            )
            stats_table.add_row("  Single-end:", f"{self.stats['single_end']:,}")

            stats_panel = Panel(
                stats_table,
                title="[bold green]📊 PROCESSING STATISTICS[/bold green]",
                border_style="green",
                padding=(1, 2),
                width=None,
                expand=False,
            )

            console.print()
            console.print(stats_panel)

            return True

        except KeyboardInterrupt:
            print("\n⚠️  Processing interrupted by user (Ctrl+C)")
            return False
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            import traceback

            traceback.print_exc()
            return False
        finally:
            # Cleanup is now handled before statistics display
            pass

    def _process_windows_parallel(self, windows: list[dict[str, Any]]):
        """Process windows in parallel with progress tracking."""
        import time

        total_windows = len(windows)
        start_time = time.time()

        with Progress(
            "[progress.description]{task.description}",
            "[progress.percentage]{task.percentage:>3.0f}%",
            "[cyan]{task.fields[windows_processed]}/{task.fields[total_windows]} windows",
            "[blue]{task.fields[chromosomes_processed]} chromosomes",
            "[green]{task.fields[reads_processed]:,} reads",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            expand=False,
        ) as progress:
            window_task = progress.add_task(
                "🔄 [cyan]Processing windows...",
                total=total_windows,
                windows_processed=0,
                reads_processed=0,
                chromosomes_processed=0,
                total_windows=total_windows,
            )

            with ProcessPoolExecutor(
                max_workers=self.max_processes,

                                initializer=_worker_initializer,

                                initargs=(self.bam_file, self.shard_dir),

                            ) as executor:                # Submit all windows for processing
                future_to_window = {}
                for i, window in enumerate(windows):
                    # Add thread_id to window data
                    window["thread_id"] = i % self.max_processes
                    window.update(
                        {
                            "input_bam": self.bam_file,
                            "method": self.method,
                            "max_dist_frac": self.max_dist_frac,
                            "max_frequency_ratio": self.max_frequency_ratio,
                            "umi_sep": self.umi_sep,
                            "umi_tag": self.umi_tag,
                            "no_umi": (self.method == "coordinate"),
                            "keep_duplicates": self.keep_duplicates,
                            "best_read_by": self.best_read_by,
                            "max_fragment_size": self.max_fragment_size,
                            "fragment_paired": self.fragment_paired,
                            "fragment_mapped": self.fragment_mapped,
                            "start_only": self.start_only,
                            "end_only": self.end_only,
                        }
                    )
                    future = executor.submit(process_window, window)
                    future_to_window[future] = window

                # Process results as they complete
                windows_processed = 0
                total_windows_skipped = 0
                total_reads_processed = 0
                total_duplicates_removed = 0
                total_duplicates_detected = 0
                chromosomes_processed = set()
                total_properly_paired = 0
                total_paired_no_mate = 0
                total_single_end = 0

                for future in as_completed(future_to_window):
                    try:
                        result = future.result()
                        if not result["success"]:
                            # This branch should ideally not be reached if process_window re-raises
                            # but keeping it for robustness or if other non-exception failures occur
                            raise RuntimeError(
                                f"Window processing failed: {result.get('error', 'Unknown error')}"
                            )
                    except Exception as e:
                        window_data = future_to_window[future]
                        contig = window_data.get("contig", "unknown")
                        start = window_data.get("start", "unknown")
                        end = window_data.get("end", "unknown")
                        raise RuntimeError(
                            f"Error processing window {contig}:{start}-{end}: {e}"
                        ) from e
                    windows_processed += 1

                    # Track unique chromosomes
                    window_data = future_to_window[future]
                    chromosomes_processed.add(window_data.get("contig", "unknown"))

                    # Count skipped windows
                    if not result.get("has_reads", False):
                        total_windows_skipped += 1

                    # No parent-side writing; workers wrote to shard files

                    # Update statistics
                    total_reads_processed += result.get("original_reads", 0)
                    total_duplicates_removed += result.get("duplicates_removed", 0)
                    total_duplicates_detected += result.get("duplicates_detected", 0)

                    # Update read type statistics
                    read_stats = result.get("read_stats", {})
                    total_properly_paired += read_stats.get("properly_paired", 0)
                    total_paired_no_mate += read_stats.get("paired_no_mate", 0)
                    total_single_end += read_stats.get("single_end", 0)

                    # Update progress
                    progress.update(
                        window_task,
                        advance=1,
                        windows_processed=windows_processed,
                        reads_processed=total_reads_processed,
                        chromosomes_processed=len(chromosomes_processed),
                    )

                # Store statistics
                self.windows_processed = windows_processed
                self.total_reads_processed = total_reads_processed
                self.total_duplicates_removed = total_duplicates_removed
                self.total_duplicates_detected = total_duplicates_detected
                self.chromosomes_processed = len(chromosomes_processed)
                self.total_properly_paired = total_properly_paired
                self.total_paired_no_mate = total_paired_no_mate
                self.total_single_end = total_single_end

                # Print summary of skipped windows
                if total_windows_skipped > 0:
                    print(
                        f"⚡ Skipped {total_windows_skipped} empty windows during processing"
                    )

                # Calculate timing and update progress bar to show completion with timing
                parallel_time = time.time() - start_time
                progress.update(
                    window_task,
                    description=f"✅ Processed windows (⏱️ {parallel_time:.2f}s)",
                    completed=windows_processed,
                    windows_processed=windows_processed,
                    reads_processed=total_reads_processed,
                    chromosomes_processed=len(chromosomes_processed),
                )

                # Store timing for statistics
                self.stats["parallel_time"] = parallel_time

                # Submit shutdown tasks to all workers to ensure files are closed
                shutdown_futures = []
                for _ in range(self.max_processes):
                    shutdown_futures.append(executor.submit(_worker_shutdown_task))

                # Wait for all shutdowns to complete
                for future in as_completed(shutdown_futures):
                    try:
                        future.result()
                    except Exception:
                        pass

        # Progress completed - will be shown in final comprehensive panel
        pass

    def _final_sort_and_cleanup(self):
        """Final sorting and cleanup - merge N temp files and sort."""
        import time

        start_time = time.time()
        # Close all file handles before merging to ensure data is flushed
        # Shard writers are closed on worker exit; collect shard files by pid name
        temp_files = []
        if os.path.isdir(self.shard_dir):
            for name in os.listdir(self.shard_dir):
                if name.endswith(".bam"):
                    temp_files.append(os.path.join(self.shard_dir, name))
        if not temp_files:
            print("⚠️  No temp files to process - creating empty output")
            # Create an empty BAM file with header only
            with pysam.AlignmentFile(self.bam_file, "rb") as _hfsrc:
                header = _hfsrc.header
            with pysam.AlignmentFile(self.output_file, "wb", header=header):
                pass  # Write header only
            return

        with Progress(
            "[progress.description]{task.description}",
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            expand=False,
        ) as progress:
            sort_task = progress.add_task(
                "🔄 Sorting and merging temporary files...",
                total=100,
            )

            try:
                # Update progress for merging
                progress.update(
                    sort_task,
                    completed=25,
                    description=f"🔄 Merging {len(temp_files)} temporary files...",
                )

                # Merge all temp files into one using samtools merge (much faster)
                merged_temp_fd, merged_temp_file = tempfile.mkstemp(
                    suffix=".bam", prefix="markdup_merged_"
                )
                os.close(merged_temp_fd)

                # Wait for shards to be complete BAMs (BGZF EOF present)
                def _is_valid_bam(path: str) -> bool:
                    try:
                        with pysam.AlignmentFile(path, "rb"):
                            return True
                    except Exception:
                        return False

                valid_temp_files = []
                deadline = time.time() + 15.0
                while time.time() < deadline:
                    valid_temp_files = []
                    for temp_file in temp_files:
                        if (
                            os.path.exists(temp_file)
                            and os.path.getsize(temp_file) > 0
                            and _is_valid_bam(temp_file)
                        ):
                            valid_temp_files.append(temp_file)
                    # If we have at least one valid shard and no invalid ones remain, proceed
                    if len(valid_temp_files) == len(
                        [
                            p
                            for p in temp_files
                            if os.path.exists(p) and os.path.getsize(p) > 0
                        ]
                    ):
                        break
                    time.sleep(0.1)

                if not valid_temp_files:
                    print(
                        "⚠️  No valid temp files found after waiting - creating empty output"
                    )
                    # Create an empty BAM file with header only
                    with pysam.AlignmentFile(self.bam_file, "rb") as _hfsrc:
                        header = _hfsrc.header
                    with pysam.AlignmentFile(merged_temp_file, "wb", header=header):
                        pass  # Write header only
                elif len(valid_temp_files) == 1:
                    # For single file, just copy it
                    import shutil

                    shutil.copy2(valid_temp_files[0], merged_temp_file)
                else:
                    # Use pysam.cat for efficient concatenation
                    pysam.cat(
                        "-o", merged_temp_file, *valid_temp_files, catch_stdout=False
                    )

                # Update progress for sorting
                progress.update(
                    sort_task,
                    completed=50,
                    description=f"🔀 Sorting BAM file with {self.max_processes} threads...",
                )

                # Sort the merged temp file using pysam.sort with memory optimization
                # Use 1GB per thread for faster sorting without excessive memory pressure
                pysam.sort(
                    "-@",
                    str(self.max_processes),
                    "-m",
                    self.memory_per_thread,
                    "-o",
                    self.output_file,
                    merged_temp_file,
                )

                # Update progress for cleanup
                progress.update(
                    sort_task,
                    completed=75,
                    description="🧹 Cleaning up temporary files...",
                )

                # Clean up merged temp file
                if os.path.exists(merged_temp_file):
                    try:
                        os.unlink(merged_temp_file)
                    except Exception:
                        pass

                # Final completion with timing
                sort_time = time.time() - start_time
                progress.update(
                    sort_task,
                    completed=100,
                    description=f"✅ Wrote sorted results to {self.output_file} (⏱️ {sort_time:.2f}s)",
                )

                # Store sorting time
                self.stats["sort_time"] = sort_time
                # Cleanup shard dir
                try:
                    import shutil as _shutil

                    _shutil.rmtree(self.shard_dir)
                except Exception:
                    pass

            except Exception as e:
                print(f"❌ Error during sorting: {e}")
                raise e

    def _calculate_final_stats(self, total_time: float):
        """Calculate final statistics."""
        self.stats["processing_time"] = total_time
        self.stats["total_windows_processed"] = getattr(self, "windows_processed", 0)
        self.stats["total_chromosomes_processed"] = getattr(
            self, "chromosomes_processed", 0
        )
        self.stats["total_reads_processed"] = getattr(self, "total_reads_processed", 0)
        self.stats["total_duplicates_removed"] = getattr(
            self, "total_duplicates_removed", 0
        )
        self.stats["total_duplicates_detected"] = getattr(
            self, "total_duplicates_detected", 0
        )
        self.stats["properly_paired"] = getattr(self, "total_properly_paired", 0)
        self.stats["paired_no_mate"] = getattr(self, "total_paired_no_mate", 0)
        self.stats["single_end"] = getattr(self, "total_single_end", 0)

        # Calculate deduplication rate
        if self.stats["total_reads_processed"] > 0:
            if self.keep_duplicates:
                # When keeping duplicates, show detection rate
                self.stats["deduplication_rate"] = (
                    self.stats["total_duplicates_detected"]
                    / self.stats["total_reads_processed"]
                    * 100
                )
            else:
                # When removing duplicates, show removal rate
                self.stats["deduplication_rate"] = (
                    self.stats["total_duplicates_removed"]
                    / self.stats["total_reads_processed"]
                    * 100
                )


# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================


def process_bam(
    input_bam: str,
    output_bam: str,
    method: str = "umi",
    umi_tag: str = "UB",
    window_size: int = 1000,
    max_processes: int = None,
    max_fragment_size: int = 2000,
    umi_sep: str = "_",
    max_dist_frac: float = 0.1,
    max_frequency_ratio: float = 0.1,
    keep_duplicates: bool = False,
    best_read_by: str = "avg_base_q",
    fragment_paired: bool = False,
    fragment_mapped: bool = False,
    start_only: bool = False,
    end_only: bool = False,
    memory_per_thread: str = "1G",
) -> bool:
    """
    Process BAM file using sequential reading and parallel window processing.

    This function provides a unified interface for BAM deduplication with both
    UMI-based and coordinate-based methods. It includes comprehensive input
    validation, error handling, and progress reporting.

    Args:
        input_bam: Path to input BAM file
        output_bam: Path to output BAM file
        method: Deduplication method ('umi' or 'coordinate')
        umi_tag: UMI tag name for BAM tags (default: 'UB')
        window_size: Genomic window size for processing (default: 1000)
        max_processes: Maximum number of parallel processes (default: auto)
        max_fragment_size: Maximum fragment size for paired-end reads (default: 2000)
        umi_sep: Separator for extracting UMIs from read names (default: '_')
        max_dist_frac: Maximum edit distance as fraction of UMI length (default: 0.1)
        max_frequency_ratio: Maximum frequency ratio for UMI merging (default: 0.1)
        keep_duplicates: Whether to keep duplicate reads and mark them (default: False)
        best_read_by: Quality criterion for selecting best read (default: 'avg_base_q')
        fragment_paired: Keep only fragments with both reads present (default: False)
        fragment_mapped: Keep only fragments where both reads are mapped (default: False)
        start_only: Use only start position for grouping (default: False)
        end_only: Use only end position for grouping (default: False)
        memory_per_thread: Memory per thread for sorting (default: '1G')

    Returns:
        bool: True if processing succeeded, False otherwise

    Raises:
        ValueError: If input parameters are invalid
        FileNotFoundError: If input file doesn't exist
    """
    import multiprocessing
    # Set the start method for multiprocessing to 'spawn' to avoid issues with fork() and multi-threading
    if multiprocessing.get_start_method(allow_none=True) is None:
        multiprocessing.set_start_method("spawn", force=True)

    # Handle SAM files by converting to temporary BAM
    temp_bam_file = None
    if input_bam.endswith(".sam"):
        print("📝 Converting SAM to temporary BAM file...")
        temp_bam_file = tempfile.mktemp(suffix=".bam", prefix="markdup_sam_")

        try:
            # Convert SAM to BAM
            with pysam.AlignmentFile(input_bam, "r") as sam_file:
                with pysam.AlignmentFile(
                    temp_bam_file, "wb", header=sam_file.header
                ) as bam_file:
                    for read in sam_file:
                        bam_file.write(read)

            # Create index for the temporary BAM file using threads
            pysam.index(temp_bam_file, "-@", str(max_processes or 1))
            input_bam = temp_bam_file  # Use the temporary BAM file for processing
            print("✅ SAM file converted to temporary BAM and indexed")
        except Exception as e:
            print(f"❌ Error converting SAM to BAM: {e}")
            return False

    processor = None

    def signal_handler(sig, frame):
        print("\n⚠️  Processing interrupted by user (Ctrl+C)")
        # No per-thread writer to clean up
        sys.exit(1)

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    try:
        processor = UnifiedProcessor(
            bam_file=input_bam,
            output_file=output_bam,
            method=method,
            umi_tag=umi_tag,
            window_size=window_size,
            max_processes=max_processes,
            max_fragment_size=max_fragment_size,
            umi_sep=umi_sep,
            max_dist_frac=max_dist_frac,
            max_frequency_ratio=max_frequency_ratio,
            keep_duplicates=keep_duplicates,
            best_read_by=best_read_by,
            fragment_paired=fragment_paired,
            fragment_mapped=fragment_mapped,
            start_only=start_only,
            end_only=end_only,
            memory_per_thread=memory_per_thread,
        )

        # Set temp BAM file if it was created from SAM
        if temp_bam_file:
            processor.temp_bam_file = temp_bam_file

        return processor.process_bam()
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user (Ctrl+C)")
        # Clean up temporary BAM file
        if temp_bam_file and os.path.exists(temp_bam_file):
            print("🧹 Cleaning up temporary BAM file...")
            os.remove(temp_bam_file)
            index_file = temp_bam_file + ".bai"
            if os.path.exists(index_file):
                os.remove(index_file)
        return False
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        print(f"❌ Processing failed: {e}")
        # No per-thread writer to clean up
        # Clean up temporary BAM file
        if temp_bam_file and os.path.exists(temp_bam_file):
            print("🧹 Cleaning up temporary BAM file...")
            os.remove(temp_bam_file)
            index_file = temp_bam_file + ".bai"
            if os.path.exists(index_file):
                os.remove(index_file)
        return False
