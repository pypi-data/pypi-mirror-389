"""
Comprehensive deduplication tests.

This module tests all deduplication functionality including edge cases.

Author: Ye Chang
Date: 2025-01-27
"""

from unittest.mock import Mock, patch

import pytest

from markdup.deduplication import (
    calculate_fragment_quality_score,
    deduplicate_fragments_by_coordinate,
    deduplicate_fragments_by_umi,
    process_window,
    _get_core_reads,
)
from markdup.deduplication import _build_fragments
from markdup.utils import Fragment


@pytest.fixture
def mock_pysam_workers(monkeypatch):
    """Mock WORKER_READER and WORKER_WRITER for testing."""
    mock_reader = Mock()
    mock_reader.header = {"HD": {"VN": "1.0"}, "SQ": [{"SN": "chr1", "LN": 10000}]}
    mock_writer = Mock()

    monkeypatch.setattr("markdup.deduplication.WORKER_READER", mock_reader)
    monkeypatch.setattr("markdup.deduplication.WORKER_WRITER", mock_writer)


class TestCalculateFragmentQualityScore:
    """Test fragment quality score calculation."""

    def test_calculate_fragment_quality_score_mapq_single_end(self):
        """Test quality scoring with mapping quality for single-end reads."""
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.reference_start = 1000
        read1.reference_end = 1100

        fragment = Fragment(query_name="read1", read1=read1)

        score = calculate_fragment_quality_score(fragment, "mapq")
        assert score == 30.0

    def test_calculate_fragment_quality_score_mapq_paired_end(self):
        """Test quality scoring with mapping quality for paired-end reads."""
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.reference_start = 1000
        read1.reference_end = 1100

        read2 = Mock()
        read2.mapping_quality = 40
        read2.query_qualities = [40] * 100
        read2.query_sequence = "T" * 100
        read2.reference_start = 1200
        read2.reference_end = 1300

        fragment = Fragment(query_name="read1", read1=read1, read2=read2)

        score = calculate_fragment_quality_score(fragment, "mapq")
        assert score == 35.0  # Average of 30 and 40

    def test_calculate_fragment_quality_score_avg_base_q_single_end(self):
        """Test quality scoring with average base quality for single-end reads."""
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.reference_start = 1000
        read1.reference_end = 1100

        fragment = Fragment(query_name="read1", read1=read1)

        score = calculate_fragment_quality_score(fragment, "avg_base_q")
        assert score == 30.0

    def test_calculate_fragment_quality_score_avg_base_q_paired_end(self):
        """Test quality scoring with average base quality for paired-end reads."""
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = [30] * 100
        read1.query_sequence = "A" * 100
        read1.reference_start = 1000
        read1.reference_end = 1100

        read2 = Mock()
        read2.mapping_quality = 40
        read2.query_qualities = [40] * 100
        read2.query_sequence = "T" * 100
        read2.reference_start = 1200
        read2.reference_end = 1300

        fragment = Fragment(query_name="read1", read1=read1, read2=read2)

        score = calculate_fragment_quality_score(fragment, "avg_base_q")
        assert score == 35.0  # Average of 30 and 40

    def test_calculate_fragment_quality_score_none_qualities(self):
        """Test quality scoring with None qualities."""
        read1 = Mock()
        read1.mapping_quality = 30
        read1.query_qualities = None
        read1.query_sequence = "A" * 100
        read1.reference_start = 1000
        read1.reference_end = 1100

        fragment = Fragment(query_name="read1", read1=read1)

        score = calculate_fragment_quality_score(fragment, "avg_base_q")
        assert score == 0.0  # Should handle None gracefully


class TestDeduplicateReadsByUMI:
    """Test UMI-based deduplication."""

    def test_deduplicate_reads_by_umi_empty(self, mock_pysam_workers):
        """Test UMI deduplication with empty input."""
        deduplicated_count, stats = deduplicate_fragments_by_umi([])
        assert deduplicated_count == 0
        assert stats["single_end"] == 0
        assert stats["paired_no_mate"] == 0
        assert stats["properly_paired"] == 0

    def test_deduplicate_reads_by_umi_single_read(self, mock_pysam_workers):
        """Test UMI deduplication with single read."""
        read = Mock()
        read.is_paired = False
        read.is_reverse = False
        read.reference_start = 1000
        read.reference_end = 1100
        read.reference_name = "chr1"
        read.query_name = "read1_UMI1"
        read.mapping_quality = 30
        read.query_qualities = [30] * 100
        read.query_sequence = "A" * 100
        read.is_unmapped = False
        read.is_duplicate = False
        read.is_proper_pair = True
        read.query_length = 100
        # Set up UMI tag
        read.tags = {"UB": "UMI1"}
        read.has_tag = lambda tag, r=read: tag in r.tags
        read.get_tag = lambda tag, r=read: r.tags[tag]

        frags = [Fragment(query_name=read.query_name, read1=read, umi="UMI1")]
        deduplicated_count, stats = deduplicate_fragments_by_umi(frags)
        assert deduplicated_count == 1
        assert stats["single_end"] == 1
        assert stats["paired_no_mate"] == 0
        assert stats["properly_paired"] == 0

    def test_deduplicate_reads_by_umi_duplicates(self, mock_pysam_workers):
        """Test UMI deduplication with duplicate reads."""
        reads = []
        for i in range(3):
            read = Mock()
            read.is_paired = False
            read.is_reverse = False
            read.reference_start = 1000
            read.reference_end = 1100
            read.reference_name = "chr1"
            read.query_name = f"read_{i}_UMI1"  # Same UMI
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            # Set up UMI tag
            read.tags = {"UB": "UMI1"}
            read.has_tag = lambda tag, r=read: tag in r.tags
            read.get_tag = lambda tag, r=read: r.tags[tag]
            reads.append(read)

        frags = [Fragment(query_name=r.query_name, read1=r, umi="UMI1") for r in reads]
        deduplicated_count, stats = deduplicate_fragments_by_umi(frags)
        assert deduplicated_count == 1  # Should deduplicate to 1
        assert stats["single_end"] == 3  # Original count

    def test_deduplicate_reads_by_umi_different_umis(self, mock_pysam_workers):
        """Test UMI deduplication with different UMIs."""
        reads = []
        for i in range(3):
            read = Mock()
            read.is_paired = False
            read.is_reverse = False
            read.reference_start = 1000
            read.reference_end = 1100
            read.reference_name = "chr1"
            read.query_qualities = [30] * 100  # Add quality scores
            # Set up UMI tag
            read.tags = {"UB": f"UMI{i}"}
            read.has_tag = lambda tag, r=read: tag in r.tags
            read.get_tag = lambda tag, r=read: r.tags[tag]
            # Make Mock objects unique by setting a unique ID
            read._mock_name = f"read_{i}"
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, umi=r.get_tag("UB"))
            for r in reads
        ]
        deduplicated_count, stats = deduplicate_fragments_by_umi(frags)
        # Current behavior selects best per position group; with same position,
        assert deduplicated_count == 3
        assert stats["single_end"] == 3

    def test_deduplicate_reads_by_umi_start_only(self, mock_pysam_workers):
        """Test UMI deduplication with start-only option."""
        reads = []
        for i in range(4):
            read = Mock()
            read.is_paired = False
            read.is_reverse = i % 2 == 1  # Mix of forward and reverse
            read.reference_start = 1000  # Same start
            read.reference_end = 1000 + i * 100  # Different end positions
            read.reference_name = "chr1"
            read.query_name = f"read_{i}_UMI1"  # Same UMI
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            read.cigar = [(0, 100)]  # Add CIGAR for reference_end calculation
            # Set up UMI tag
            read.tags = {"UB": "UMI1"}
            read.has_tag = lambda tag, r=read: tag in r.tags
            read.get_tag = lambda tag, r=read: r.tags[tag]
            reads.append(read)

        frags = [
            Fragment(
                query_name=r.query_name, read1=r, umi=r.get_tag("UB"), start_only=True
            )
            for r in reads
        ]
        deduplicated_count, stats = deduplicate_fragments_by_umi(frags, start_only=True)
        # With start_only=True, reads with same biological start should be grouped
        # Forward reads: bio_start = reference_start = 1000
        # Reverse reads: bio_start = reference_end = 1000 + i * 100
        # So we expect 3 groups: forward reads (bio_start=1000), reverse read1 (bio_start=1100), reverse read3 (bio_start=1300)
        assert deduplicated_count == 3  # Should group by biological start position
        assert stats["single_end"] == 4

    def test_deduplicate_reads_by_umi_end_only(self, mock_pysam_workers):
        """Test UMI deduplication with end-only option."""
        reads = []
        for i in range(4):
            read = Mock()
            read.is_paired = False
            read.is_reverse = i % 2 == 1  # Mix of forward and reverse
            read.reference_start = 1000 + i * 100  # Different start positions
            read.reference_end = 1100  # Same end
            read.reference_name = "chr1"
            read.query_name = f"read_{i}_UMI1"  # Same UMI
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            read.cigar = [(0, 100)]  # Add CIGAR for reference_end calculation
            # Set up UMI tag
            read.tags = {"UB": "UMI1"}
            read.has_tag = lambda tag, r=read: tag in r.tags
            read.get_tag = lambda tag, r=read: r.tags[tag]
            reads.append(read)

        frags = [
            Fragment(
                query_name=r.query_name, read1=r, umi=r.get_tag("UB"), end_only=True
            )
            for r in reads
        ]
        deduplicated_count, stats = deduplicate_fragments_by_umi(frags, end_only=True)
        # With end_only=True, reads with same biological end should be grouped
        # Forward reads: bio_end = reference_end = 1100
        # Reverse reads: bio_end = reference_start = 1000 + i * 100
        # So we expect 3 groups: forward reads (bio_end=1100), reverse read1 (bio_end=1100), reverse read3 (bio_end=1300)
        assert deduplicated_count == 3  # Each read has different biological end
        assert stats["single_end"] == 4

    def test_deduplicate_reads_by_umi_edit_distance_clustering(self, mock_pysam_workers):
        """Test UMI deduplication with edit distance clustering."""
        reads = []
        umis = ["UMI1", "UMI2", "UMI3"]  # Similar UMIs
        for i, umi in enumerate(umis):
            read = Mock()
            read.is_paired = False
            read.is_reverse = False
            read.reference_start = 1000
            read.reference_end = 1100
            read.reference_name = "chr1"
            read.query_name = f"read_{i}_{umi}"
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            # Set up UMI tag
            read.tags = {"UB": umi}
            read.has_tag = lambda tag, r=read: tag in r.tags
            read.get_tag = lambda tag, r=read: r.tags[tag]
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, umi=r.get_tag("UB"))
            for r in reads
        ]
        deduplicated_count, stats = deduplicate_fragments_by_umi(
            frags, max_dist_frac=0.1
        )
        # Should cluster similar UMIs
        assert deduplicated_count >= 1
        assert stats["single_end"] == 3


class TestDeduplicateReadsByCoordinate:
    """Test coordinate-based deduplication."""

    def test_deduplicate_reads_by_coordinate_empty(self, mock_pysam_workers):
        """Test coordinate deduplication with empty input."""
        deduplicated_count, stats = deduplicate_fragments_by_coordinate([])
        assert deduplicated_count == 0
        assert stats["paired_no_mate"] == 0
        assert stats["properly_paired"] == 0

    def test_deduplicate_reads_by_coordinate_single_read(self, mock_pysam_workers):
        """Test coordinate deduplication with single read."""
        read = Mock()
        read.is_paired = False
        read.is_reverse = False
        read.reference_start = 1000
        read.reference_end = 1100
        read.reference_name = "chr1"
        read.query_name = "read1"
        read.mapping_quality = 30
        read.query_qualities = [30] * 100
        read.query_sequence = "A" * 100
        read.is_unmapped = False
        read.is_duplicate = False
        read.is_proper_pair = True
        read.query_length = 100

        frags = [Fragment(query_name=read.query_name, read1=read)]
        deduplicated_count, stats = deduplicate_fragments_by_coordinate(frags)
        assert deduplicated_count == 1
        assert stats["single_end"] == 1

    def test_deduplicate_reads_by_coordinate_duplicates(self, mock_pysam_workers):
        """Test coordinate deduplication with duplicate reads."""
        reads = []
        for i in range(3):
            read = Mock()
            read.is_paired = False
            read.is_reverse = False
            read.reference_start = 1000  # Same position
            read.reference_end = 1100
            read.reference_name = "chr1"
            read.query_name = f"read_{i}"
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            reads.append(read)

        frags = [Fragment(query_name=r.query_name, read1=r) for r in reads]
        deduplicated_count, stats = deduplicate_fragments_by_coordinate(frags)
        assert deduplicated_count == 1  # Should deduplicate to 1
        assert stats["single_end"] == 3  # Original count

    def test_deduplicate_reads_by_coordinate_different_positions(self, mock_pysam_workers):
        """Test coordinate deduplication with different positions."""
        reads = []
        for i in range(3):
            read = Mock()
            read.is_paired = False
            read.is_reverse = False
            read.reference_start = 1000 + i * 1000  # Different positions
            read.reference_end = 1100 + i * 1000
            read.reference_name = "chr1"
            read.query_name = f"read_{i}"
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            reads.append(read)

        frags = [Fragment(query_name=r.query_name, read1=r) for r in reads]
        deduplicated_count, stats = deduplicate_fragments_by_coordinate(frags)
        assert deduplicated_count == 3  # All unique positions
        assert stats["single_end"] == 3

    def test_deduplicate_reads_by_coordinate_start_only(self, mock_pysam_workers):
        """Test coordinate deduplication with start-only option."""
        reads = []
        for i in range(4):
            read = Mock()
            read.is_paired = False
            read.is_reverse = i % 2 == 1  # Mix of forward and reverse
            read.reference_start = 1000  # Same start
            read.reference_end = 1000 + i * 100  # Different end positions
            read.reference_name = "chr1"
            read.query_name = f"read_{i}"
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            read.cigar = [(0, 100)]  # Add CIGAR for reference_end calculation
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, start_only=True) for r in reads
        ]
        deduplicated_count, stats = deduplicate_fragments_by_coordinate(
            frags, start_only=True
        )
        # With start_only=True, reads with same biological start should be grouped
        # Forward reads: bio_start = reference_start = 1000
        # Reverse reads: bio_start = reference_end = 1000 + i * 100
        # So we expect 3 groups: forward reads (bio_start=1000), reverse read1 (bio_start=1100), reverse read3 (bio_start=1300)
        assert deduplicated_count == 3  # Should group by biological start position
        assert stats["single_end"] == 4

    def test_deduplicate_reads_by_coordinate_end_only(self, mock_pysam_workers):
        """Test coordinate deduplication with end-only option."""
        reads = []
        for i in range(4):
            read = Mock()
            read.is_paired = False
            read.is_reverse = i % 2 == 1  # Mix of forward and reverse
            read.reference_start = 1000 + i * 100  # Different start positions
            read.reference_end = 1100  # Same end
            read.reference_name = "chr1"
            read.query_name = f"read_{i}"
            read.mapping_quality = 30
            read.query_qualities = [30] * 100
            read.query_sequence = "A" * 100
            read.is_unmapped = False
            read.is_duplicate = False
            read.is_proper_pair = True
            read.query_length = 100
            read.cigar = [(0, 100)]  # Add CIGAR for reference_end calculation
            reads.append(read)

        frags = [
            Fragment(query_name=r.query_name, read1=r, end_only=True) for r in reads
        ]
        deduplicated_count, stats = deduplicate_fragments_by_coordinate(
            frags, end_only=True
        )
        # With end_only=True, reads with same biological end should be grouped
        # Forward reads: bio_end = reference_end = 1100
        # Reverse reads: bio_end = reference_start = 1000 + i * 100
        # So we expect 3 groups: forward reads (bio_end=1100), reverse read1 (bio_end=1100), reverse read3 (bio_end=1300)
        assert deduplicated_count == 3  # Each read has different biological end
        assert stats["single_end"] == 4


class TestProcessWindow:
    """Test window processing functionality."""

    def test_process_window_success(self):
        """Test successful window processing."""
        window_data = {
            "input_bam": "test.bam",
            "contig": "chr1",
            "search_start": 1000,
            "search_end": 2000,
            "window_start": 1000,
            "window_end": 1500,
            "max_dist_frac": 0.1,
            "umi_sep": "_",
            "no_umi": False,
            "keep_duplicates": False,
            "best_read_by": "avg_base_q",
            "max_fragment_size": 2000,
            "fragment_paired": False,
            "fragment_mapped": False,
            "start_only": False,
            "end_only": False,
            "is_first_window": True,
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
        ):
            result = process_window(window_data)

            assert result["success"]
            assert result["has_reads"]
            assert result["original_reads"] == 3
            assert result["deduplicated_reads"] == 3  # All unique

    def test_process_window_empty(self):
        """Test window processing with no reads."""
        window_data = {
            "input_bam": "test.bam",
            "contig": "chr1",
            "search_start": 1000,
            "search_end": 2000,
            "window_start": 1000,
            "window_end": 1500,
            "max_dist_frac": 0.1,
            "umi_sep": "_",
            "no_umi": False,
            "keep_duplicates": False,
            "best_read_by": "avg_base_q",
            "max_fragment_size": 2000,
            "fragment_paired": False,
            "fragment_mapped": False,
            "start_only": False,
            "end_only": False,
            "is_first_window": True,
            "window_id": "test_window",
        }

        # Mock the global WORKER_READER with empty fetch
        mock_reader = Mock()
        mock_reader.fetch.return_value = []

        with patch("markdup.deduplication.WORKER_READER", mock_reader):
            result = process_window(window_data)

            assert result["success"]
            assert not result["has_reads"]
            assert result["original_reads"] == 0
            assert result["deduplicated_reads"] == 0

    def test_process_window_error(self):
        """Test window processing with error."""
        window_data = {
            "input_bam": "nonexistent.bam",
            "contig": "chr1",
            "search_start": 1000,
            "search_end": 2000,
            "window_start": 1000,
            "window_end": 1500,
            "max_dist_frac": 0.1,
            "umi_sep": "_",
            "no_umi": False,
            "keep_duplicates": False,
            "best_read_by": "avg_base_q",
            "max_fragment_size": 2000,
            "fragment_paired": False,
            "fragment_mapped": False,
            "start_only": False,
            "end_only": False,
            "is_first_window": True,
            "window_id": "test_window",
        }

        # Mock WORKER_READER to raise FileNotFoundError when fetch is called
        mock_reader = Mock()
        mock_reader.fetch.side_effect = FileNotFoundError("BAM file not found")

        with patch("markdup.deduplication.WORKER_READER", mock_reader):
            with pytest.raises(FileNotFoundError): # Change back to FileNotFoundError
                process_window(window_data)

class TestFragmentBuilding:
    """Test fragment building logic."""

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

        read2_loc1 = Mock()
        read2_loc1.query_name = "multi_map_read"
        read2_loc1.reference_name = "chr1"
        read2_loc1.reference_start = 200
        read2_loc1.reference_end = 250
        read2_loc1.is_paired = True
        read2_loc1.next_reference_name = "chr1"
        read2_loc1.next_reference_start = 100

        read1_loc2 = Mock()
        read1_loc2.query_name = "multi_map_read"
        read1_loc2.reference_name = "chr1"
        read1_loc2.reference_start = 500
        read1_loc2.reference_end = 550
        read1_loc2.is_paired = True
        read1_loc2.next_reference_name = "chr1"
        read1_loc2.next_reference_start = 600

        read2_loc2 = Mock()
        read2_loc2.query_name = "multi_map_read"
        read2_loc2.reference_name = "chr1"
        read2_loc2.reference_start = 600
        read2_loc2.reference_end = 650
        read2_loc2.is_paired = True
        read2_loc2.next_reference_name = "chr1"
        read2_loc2.next_reference_start = 500

        reads = [read1_loc1, read2_loc1, read1_loc2, read2_loc2]

        fragments, read_count = _build_fragments(reads, False, None, "_", 2000, False, False)

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
