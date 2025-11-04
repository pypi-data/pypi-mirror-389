"""
Comprehensive deduplication tests.

This module tests all deduplication functionality including edge cases.

Author: Ye Chang
Date: 2025-01-27
"""

from unittest.mock import Mock, patch

import pysam
import pytest

from markdup.deduplication import (
    _build_fragments,
    calculate_fragment_quality_score,
    deduplicate_fragments_by_coordinate,
    deduplicate_fragments_by_umi,
    process_window,
)
from markdup.utils import Fragment


@pytest.fixture
def mock_pysam_workers(monkeypatch):
    """Mock WORKER_READER/WRITER and shard path for tests that write."""
    mock_reader = Mock()
    mock_reader.header = {"HD": {"VN": "1.0"}, "SQ": [{"SN": "chr1", "LN": 10000}]}
    mock_writer = Mock()

    monkeypatch.setattr("markdup.deduplication.WORKER_READER", mock_reader, raising=False)
    monkeypatch.setattr("markdup.deduplication.WORKER_WRITER", mock_writer, raising=False)
    monkeypatch.setattr("markdup.deduplication.WORKER_SHARD_PATH", "/tmp/test_shard.bam", raising=False)


class TestCalculateFragmentQualityScore:
    """Test fragment quality score calculation."""

    def test_calculate_fragment_quality_score_mapq_single_end(self):
        """Test quality scoring with mapping quality for single-end reads."""
        from unittest.mock import Mock
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.is_paired = False
        fragment = Fragment(query_name="read1", read1=read1)
        score = calculate_fragment_quality_score(fragment, "mapq")
        assert score == 30.0

    def test_calculate_fragment_quality_score_mapq_paired_end(self):
        """Test quality scoring with mapping quality for paired-end reads."""
        from unittest.mock import Mock
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.is_paired = True
        read1.reference_start = 1000
        read1.reference_end = 1100
        read2 = Mock()
        read2.mapping_quality = 40
        read2.query_qualities = [40] * 100
        read2.query_sequence = "A" * 100
        read2.is_paired = True
        read2.reference_start = 1200
        read2.reference_end = 1300
        fragment = Fragment(query_name="read1", read1=read1, read2=read2)
        score = calculate_fragment_quality_score(fragment, "mapq")
        assert score == 35.0  # Average of 30 and 40

    def test_calculate_fragment_quality_score_avg_base_q_single_end(self):
        """Test quality scoring with average base quality for single-end reads."""
        from unittest.mock import Mock
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.is_paired = False
        fragment = Fragment(query_name="read1", read1=read1)
        score = calculate_fragment_quality_score(fragment, "avg_base_q")
        assert score == 30.0

    def test_calculate_fragment_quality_score_avg_base_q_paired_end(self):
        """Test quality scoring with average base quality for paired-end reads."""
        from unittest.mock import Mock
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.is_paired = True
        read1.reference_start = 1000
        read1.reference_end = 1100
        read2 = Mock()
        read2.mapping_quality = 40
        read2.query_qualities = [40] * 100
        read2.query_sequence = "A" * 100
        read2.is_paired = True
        read2.reference_start = 1200
        read2.reference_end = 1300
        fragment = Fragment(query_name="read1", read1=read1, read2=read2)
        score = calculate_fragment_quality_score(fragment, "avg_base_q")
        assert score == 35.0  # Average of 30 and 40

    def test_calculate_fragment_quality_score_none_qualities(self):
        """Test quality scoring with None qualities."""
        from unittest.mock import Mock
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = None
        read1.query_sequence = "A" * 100
        read1.is_paired = False
        fragment = Fragment(query_name="read1", read1=read1)
        score = calculate_fragment_quality_score(fragment, "avg_base_q")
        assert score == 0.0  # Should handle None gracefully


class TestDeduplicateReadsByUMI:
    """Test UMI-based deduplication."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_pysam_workers):
        pass

    def test_deduplicate_reads_by_umi_empty(self):
        """Test UMI deduplication with empty input."""
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_umi([])
        assert fragments_by_class["single_end"] == 0
        assert duplicate_by_class["single_end"] == 0
        assert unmapped_by_class["single_end"] == 0

    def test_deduplicate_reads_by_umi_single_read(self):
        """Test UMI deduplication with single read."""
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        read = pysam.AlignedSegment(header)
        read.query_name = "read1_UMI1"
        read.flag = 0
        read.reference_id = 0
        read.reference_start = 1000
        read.mapping_quality = 30
        read.cigarstring = "100M"
        read.query_sequence = "A" * 100
        read.query_qualities = [30] * 100
        read.set_tag("UB", "UMI1")
        frags = [Fragment(query_name=read.query_name, read1=read, umi="UMI1", is_originally_paired=False, fragment_id="frag1")]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_umi(frags)
        assert fragments_by_class["single_end"] == 1
        assert duplicate_by_class["single_end"] == 0

    def test_deduplicate_reads_by_umi_duplicates(self):
        """Test UMI deduplication with duplicate reads."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(3):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}_UMI1"
            read.flag = 0
            read.reference_id = 0
            read.reference_start = 1000
            read.mapping_quality = 30
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30] * 100
            read.set_tag("UB", "UMI1")
            reads.append(read)

        frags = [Fragment(query_name=r.query_name, read1=r, umi="UMI1", is_originally_paired=False, fragment_id=f"frag{i}") for i, r in enumerate(reads)]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_umi(frags)
        assert fragments_by_class["single_end"] == 1
        assert duplicate_by_class["single_end"] == 2

    def test_deduplicate_reads_by_umi_different_umis(self):
        """Test UMI deduplication with different UMIs."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(3):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}_UMI{i}"
            read.flag = 0
            read.reference_id = 0
            read.reference_start = 1000
            read.mapping_quality = 30
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30] * 100
            read.set_tag("UB", f"UMI{i}")
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, umi=r.get_tag("UB"), is_originally_paired=False, fragment_id=f"frag{i}")
            for i, r in enumerate(reads)
        ]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_umi(frags)
        assert fragments_by_class["single_end"] == 3
        assert duplicate_by_class["single_end"] == 0

    def test_deduplicate_reads_by_umi_start_only(self):
        """Test UMI deduplication with start-only option."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(4):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}_UMI1"
            read.flag = 0 if i % 2 == 0 else 16
            read.reference_id = 0
            read.reference_start = 1000
            read.mapping_quality = 30
            read.cigarstring = f"{100 + i * 100}M"
            read.query_sequence = "A" * (100 + i * 100)
            read.query_qualities = [30] * (100 + i * 100)
            read.set_tag("UB", "UMI1")
            reads.append(read)

        frags = [
            Fragment(
                query_name=r.query_name, read1=r, umi=r.get_tag("UB"), start_only=True, is_originally_paired=False, fragment_id=f"frag{i}"
            )
            for i, r in enumerate(reads)
        ]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_umi(frags, start_only=True)
        assert fragments_by_class["single_end"] == 3
        assert duplicate_by_class["single_end"] == 1

    def test_deduplicate_reads_by_umi_end_only(self):
        """Test UMI deduplication with end-only option."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(4):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}_UMI1"
            read.flag = 0 if i % 2 == 0 else 16
            read.reference_id = 0
            read.reference_start = 1000 + i * 100
            read.mapping_quality = 30
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30] * 100
            read.set_tag("UB", "UMI1")
            reads.append(read)

        frags = [
            Fragment(
                query_name=r.query_name, read1=r, umi=r.get_tag("UB"), end_only=True, is_originally_paired=False, fragment_id=f"frag{i}"
            )
            for i, r in enumerate(reads)
        ]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_umi(frags, end_only=True)
        assert fragments_by_class["single_end"] == 4
        assert duplicate_by_class["single_end"] == 0

    def test_deduplicate_reads_by_umi_edit_distance_clustering(self):
        """Test UMI deduplication with edit distance clustering."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        umis = ["UMI1", "UMI2", "UMI3"]
        for i, umi in enumerate(umis):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}_{umi}"
            read.flag = 0
            read.reference_id = 0
            read.reference_start = 1000
            read.mapping_quality = 30
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30] * 100
            read.set_tag("UB", umi)
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, umi=r.get_tag("UB"), is_originally_paired=False, fragment_id=f"frag{i}")
            for i, r in enumerate(reads)
        ]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_umi(
            frags, max_dist_frac=0.1
        )
        # Frequency-aware clustering with equal frequencies keeps separate groups
        assert fragments_by_class["single_end"] == 3
        assert duplicate_by_class["single_end"] == 0


class TestDeduplicateReadsByCoordinate:
    """Test coordinate-based deduplication."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_pysam_workers):
        pass

    def test_deduplicate_reads_by_coordinate_empty(self):
        """Test coordinate deduplication with empty input."""
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_coordinate([])
        assert fragments_by_class["single_end"] == 0
        assert duplicate_by_class["single_end"] == 0
        assert unmapped_by_class["single_end"] == 0

    def test_deduplicate_reads_by_coordinate_single_read(self):
        """Test coordinate deduplication with single read."""
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        read = pysam.AlignedSegment(header)
        read.query_name = "read1"
        read.flag = 0
        read.reference_id = 0
        read.reference_start = 1000
        read.mapping_quality = 30
        read.cigarstring = "100M"
        read.query_sequence = "A" * 100
        read.query_qualities = [30] * 100
        frags = [Fragment(query_name=read.query_name, read1=read, is_originally_paired=False, fragment_id="frag1")]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_coordinate(frags)
        assert fragments_by_class["single_end"] == 1
        assert duplicate_by_class["single_end"] == 0

    def test_deduplicate_reads_by_coordinate_duplicates(self):
        """Test coordinate deduplication with duplicate reads."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(3):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}"
            read.flag = 0
            read.reference_id = 0
            read.reference_start = 1000
            read.mapping_quality = 30
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30] * 100
            reads.append(read)

        frags = [Fragment(query_name=r.query_name, read1=r, is_originally_paired=False, fragment_id=f"frag{i}") for i, r in enumerate(reads)]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_coordinate(frags)
        assert fragments_by_class["single_end"] == 1
        assert duplicate_by_class["single_end"] == 2

    def test_deduplicate_reads_by_coordinate_different_positions(self):
        """Test coordinate deduplication with different positions."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(3):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}"
            read.flag = 0
            read.reference_id = 0
            read.reference_start = 1000 + i * 1000
            read.mapping_quality = 30
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30] * 100
            reads.append(read)

        frags = [Fragment(query_name=r.query_name, read1=r, is_originally_paired=False, fragment_id=f"frag{i}") for i, r in enumerate(reads)]
        fragments_by_class, duplicate_fragments_by_class, unmapped_fragments_by_class = deduplicate_fragments_by_coordinate(frags)
        assert fragments_by_class["single_end"] == 3
        assert duplicate_fragments_by_class["single_end"] == 0
        assert unmapped_fragments_by_class["single_end"] == 0

    def test_deduplicate_reads_by_coordinate_start_only(self):
        """Test coordinate deduplication with start-only option."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(4):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}"
            read.flag = 0 if i % 2 == 0 else 16
            read.reference_id = 0
            read.reference_start = 1000
            read.mapping_quality = 30
            read.cigarstring = f"{100 + i * 100}M"
            read.query_sequence = "A" * (100 + i * 100)
            read.query_qualities = [30] * (100 + i * 100)
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, start_only=True, is_originally_paired=False, fragment_id=f"frag{i}") for i, r in enumerate(reads)
        ]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_coordinate(
            frags, start_only=True
        )
        assert fragments_by_class["single_end"] == 3
        assert duplicate_by_class["single_end"] == 1

    def test_deduplicate_reads_by_coordinate_end_only(self):
        """Test coordinate deduplication with end-only option."""
        reads = []
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        for i in range(4):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}"
            read.flag = 0 if i % 2 == 0 else 16
            read.reference_id = 0
            read.reference_start = 1000 + i * 100
            read.mapping_quality = 30
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30] * 100
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, end_only=True, is_originally_paired=False, fragment_id=f"frag{i}") for i, r in enumerate(reads)
        ]
        fragments_by_class, duplicate_by_class, unmapped_by_class = deduplicate_fragments_by_coordinate(
            frags, end_only=True
        )
        assert fragments_by_class["single_end"] == 4
        assert duplicate_by_class["single_end"] == 0


class TestProcessWindow:
    """Test window processing functionality."""

    def setup_method(self):
        from markdup.deduplication import WorkerSettings
        self.settings = WorkerSettings(
            method="umi",
            umi_tag="UB",
            umi_sep="_",
            max_dist_frac=0.1,
            max_frequency_ratio=0.1,
            keep_duplicates=False,
            best_read_by="avg_base_q",
            max_fragment_size=2000,
            fragment_paired=False,
            fragment_mapped=False,
            start_only=False,
            end_only=False,
            mark_fragment=False,
            no_umi=False,
        )

    def test_process_window_success(self):
        """Test successful window processing."""
        window_data = {
            "contig": "chr1",
            "search_start": 1000,
            "search_end": 2000,
            "window_start": 1000,
            "window_end": 1500,
            "window_id": "test_window",
        }

        # Mock the global WORKER_READER
        mock_reader = Mock()
        mock_reads = []
        for i in range(3):
            read = Mock()
            read.is_paired = False
            read.is_reverse = False
            read.reference_start = 1000 + i * 100
            read.reference_end = 1100 + i * 100
            read.reference_name = "chr1"
            read.query_name = f"read_{i}_UMI{i}"
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            read.reference_id = 0
            mock_reads.append(read)

        mock_reader.fetch.return_value = mock_reads
        mock_reader.get_tid.return_value = 0

        # Mock the global WORKER_WRITER
        mock_writer = Mock()

        with (
            patch("markdup.deduplication.WORKER_READER", mock_reader),
            patch("markdup.deduplication.WORKER_WRITER", mock_writer),
            patch("markdup.deduplication.WORKER_SHARD_PATH", "/tmp/test_shard.bam"),
            patch("markdup.deduplication.WORKER_SETTINGS", self.settings),
        ):
            result = process_window(window_data)

            assert result["success"]
            assert result["has_reads"]
            assert result["total_original_reads"] == 3
            assert result["total_unique_reads"] == 3
            assert result["total_duplicate_reads"] == 0
            assert result["fragments_by_class_single_end"] == 3
            assert result["built_frags_single_end"] == 3

    def test_process_window_empty(self):
        """Test window processing with no reads."""
        window_data = {
            "contig": "chr1",
            "search_start": 1000,
            "search_end": 2000,
            "window_start": 1000,
            "window_end": 1500,
            "window_id": "test_window",
        }

        # Mock the global WORKER_READER with empty fetch
        mock_reader = Mock()
        mock_reader.fetch.return_value = []

        with patch("markdup.deduplication.WORKER_READER", mock_reader), patch("markdup.deduplication.WORKER_SETTINGS", self.settings):
            result = process_window(window_data)

            assert result["success"]
            assert not result["has_reads"]
            assert result["total_original_reads"] == 0
            assert result["total_unique_reads"] == 0
            assert result["total_duplicate_reads"] == 0
            assert result["fragments_by_class_single_end"] == 0
            assert result["built_frags_single_end"] == 0

    def test_process_window_default_behavior(self, mock_pysam_workers):  # noqa: ARG002
        """Test window processing with default settings (no mark_fragment, no keep_duplicates)."""
        window_data = {
            "contig": "chr1",
            "search_start": 1000,
            "search_end": 2000,
            "window_start": 1000,
            "window_end": 1500,
            "window_id": "test_window_default",
        }

        # Mock the global WORKER_READER and provide pysam reads
        mock_reader = Mock()
        header = pysam.AlignmentHeader.from_references(["chr1"], [10000])
        mock_reads = []
        for i in range(3):
            read = pysam.AlignedSegment(header)
            read.query_name = f"read_{i}_UMI1"
            read.flag = 0
            read.reference_id = 0
            read.reference_start = 1000
            read.mapping_quality = 30 + i * 5
            read.cigarstring = "100M"
            read.query_sequence = "A" * 100
            read.query_qualities = [30 + i * 5] * 100
            read.set_tag("UB", "UMI1")
            mock_reads.append(read)

        mock_reader.fetch.return_value = mock_reads
        mock_reader.get_tid.return_value = 0

        # Mock the global WORKER_WRITER
        mock_writer = Mock()

        # Settings should be default (mark_fragment=False, keep_duplicates=False)
        self.settings.mark_fragment = False
        self.settings.keep_duplicates = False

        with (
            patch("markdup.deduplication.WORKER_READER", mock_reader),
            patch("markdup.deduplication.WORKER_WRITER", mock_writer),
            patch("markdup.deduplication.WORKER_SHARD_PATH", "/tmp/test_shard_default.bam"),
            patch("markdup.deduplication.WORKER_SETTINGS", self.settings),
        ):
            result = process_window(window_data)

            assert result["success"]
            assert result["has_reads"]
            assert result["total_original_reads"] == 3
            assert result["total_unique_reads"] == 1  # One unique, two duplicates removed
            assert result["total_duplicate_reads"] == 2
            assert result["fragments_by_class_single_end"] == 1
            assert result["duplicate_fragments_by_class_single_end"] == 2
            assert result["built_frags_single_end"] == 3

            # Verify that WORKER_WRITER was called only once (for the best read)
            assert mock_writer.write.call_count == 1

            # Check tags on the written read
            written_read = mock_writer.write.call_args[0][0]
            assert not written_read.is_duplicate
            # Cluster name contains reference, positions, strand, and UMI; ensure UMI present
            assert "UMI1" in written_read.get_tag("cn")
            assert written_read.get_tag("cs") == 3
            # fi tag should not be present
            with pytest.raises(KeyError):
                written_read.get_tag("fi")

    def test_process_window_error(self):
        """Test window processing with error."""
        window_data = {
            "contig": "chr1",
            "search_start": 1000,
            "search_end": 2000,
            "window_start": 1000,
            "window_end": 1500,
            "window_id": "test_window",
        }

        # Mock WORKER_READER to raise FileNotFoundError when fetch is called
        mock_reader = Mock()
        mock_reader.fetch.side_effect = FileNotFoundError("BAM file not found")

        with patch("markdup.deduplication.WORKER_READER", mock_reader), patch("markdup.deduplication.WORKER_SETTINGS", self.settings):
            with pytest.raises(FileNotFoundError):
                process_window(window_data)


class TestFragmentBuilding:
    """Test fragment building logic."""

    def test_build_fragments_multi_mapping_alt(self):
        """Test that _build_fragments correctly handles multi-mapping reads."""
        # Create a read pair with two mapping locations
        read1_loc1 = Mock()
        read1_loc1.query_name = "multi_map_read"
        read1_loc1.reference_name = "chr1"
        read1_loc1.reference_start = 100
        read1_loc1.reference_end = 150
        read1_loc1.is_paired = True
        read1_loc1.next_reference_name = "chr1"
        read1_loc1.next_reference_start = 200
        read1_loc1.reference_id = 0
        read1_loc1.next_reference_id = 0
        read1_loc1.is_unmapped = False
        read1_loc1.is_proper_pair = True

        read2_loc1 = Mock()
        read2_loc1.query_name = "multi_map_read"
        read2_loc1.reference_name = "chr1"
        read2_loc1.reference_start = 200
        read2_loc1.reference_end = 250
        read2_loc1.is_paired = True
        read2_loc1.next_reference_name = "chr1"
        read2_loc1.next_reference_start = 100
        read2_loc1.reference_id = 0
        read2_loc1.next_reference_id = 0
        read2_loc1.is_unmapped = False
        read2_loc1.is_proper_pair = True

        read1_loc2 = Mock()
        read1_loc2.query_name = "multi_map_read"
        read1_loc2.reference_name = "chr1"
        read1_loc2.reference_start = 500
        read1_loc2.reference_end = 550
        read1_loc2.is_paired = True
        read1_loc2.next_reference_name = "chr1"
        read1_loc2.next_reference_start = 600
        read1_loc2.reference_id = 0
        read1_loc2.next_reference_id = 0
        read1_loc2.is_unmapped = False
        read1_loc2.is_proper_pair = True

        read2_loc2 = Mock()
        read2_loc2.query_name = "multi_map_read"
        read2_loc2.reference_name = "chr1"
        read2_loc2.reference_start = 600
        read2_loc2.reference_end = 650
        read2_loc2.is_paired = True
        read2_loc2.next_reference_name = "chr1"
        read2_loc2.next_reference_start = 500
        read2_loc2.reference_id = 0
        read2_loc2.next_reference_id = 0
        read2_loc2.is_unmapped = False
        read2_loc2.is_proper_pair = True

        reads = [read1_loc1, read2_loc1, read1_loc2, read2_loc2]

        fragments, read_count, fragments_by_class_built, unmapped_fragments_by_class_built = _build_fragments(reads, False, None, "_", 2000, False, False)

        assert len(fragments) == 2
        assert read_count == 4
        assert fragments_by_class_built["properly_paired"] == 2
        assert unmapped_fragments_by_class_built["properly_paired"] == 0

        # Check that the two fragments have the correct read pairs
        frag1_reads = {id(fragments[0].read1), id(fragments[0].read2)}
        frag2_reads = {id(fragments[1].read1), id(fragments[1].read2)}

        assert (
            frag1_reads == {id(read1_loc1), id(read2_loc1)}
            and frag2_reads == {id(read1_loc2), id(read2_loc2)}
        ) or (
            frag1_reads == {id(read1_loc2), id(read2_loc2)}
            and frag2_reads == {id(read1_loc1), id(read2_loc1)}
        )

    def test_build_fragments_multi_mapping(self):
        """Test that _build_fragments correctly handles multi-mapping reads."""
        # Create a read pair with two mapping locations
        read1_loc1 = Mock()
        read1_loc1.query_name = "multi_map_read"
        read1_loc1.reference_name = "chr1"
        read1_loc1.reference_start = 100
        read1_loc1.reference_end = 150
        read1_loc1.is_paired = True
        read1_loc1.next_reference_name = "chr1"
        read1_loc1.next_reference_start = 200
        read1_loc1.reference_id = 0
        read1_loc1.next_reference_id = 0

        read2_loc1 = Mock()
        read2_loc1.query_name = "multi_map_read"
        read2_loc1.reference_name = "chr1"
        read2_loc1.reference_start = 200
        read2_loc1.reference_end = 250
        read2_loc1.is_paired = True
        read2_loc1.next_reference_name = "chr1"
        read2_loc1.next_reference_start = 100
        read2_loc1.reference_id = 0
        read2_loc1.next_reference_id = 0

        read1_loc2 = Mock()
        read1_loc2.query_name = "multi_map_read"
        read1_loc2.reference_name = "chr1"
        read1_loc2.reference_start = 500
        read1_loc2.reference_end = 550
        read1_loc2.is_paired = True
        read1_loc2.next_reference_name = "chr1"
        read1_loc2.next_reference_start = 600
        read1_loc2.reference_id = 0
        read1_loc2.next_reference_id = 0

        read2_loc2 = Mock()
        read2_loc2.query_name = "multi_map_read"
        read2_loc2.reference_name = "chr1"
        read2_loc2.reference_start = 600
        read2_loc2.reference_end = 650
        read2_loc2.is_paired = True
        read2_loc2.next_reference_name = "chr1"
        read2_loc2.next_reference_start = 500
        read2_loc2.reference_id = 0
        read2_loc2.next_reference_id = 0

        reads = [read1_loc1, read2_loc1, read1_loc2, read2_loc2]

        fragments, read_count, fragments_by_class_built, unmapped_fragments_by_class_built = _build_fragments(reads, False, None, "_", 2000, False, False)

        assert len(fragments) == 2
        assert read_count == 4
        # Check that the two fragments have the correct read pairs
        frag1_reads = {id(fragments[0].read1), id(fragments[0].read2)}
        frag2_reads = {id(fragments[1].read1), id(fragments[1].read2)}

        assert (
            frag1_reads == {id(read1_loc1), id(read2_loc1)}
            and frag2_reads == {id(read1_loc2), id(read2_loc2)}
        ) or (
            frag1_reads == {id(read1_loc2), id(read2_loc2)}
            and frag2_reads == {id(read1_loc1), id(read2_loc1)}
        )


if __name__ == "__main__":
    pytest.main([__file__])
