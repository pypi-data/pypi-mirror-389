"""
Simple CLI tests for BAM deduplication.

This module tests the CLI functionality with a focus on working tests.

Author: Ye Chang
Date: 2025-01-27
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from markdup.cli import validate_bam_file


class TestValidateBamFile:
    """Test BAM file validation."""

    def test_validate_bam_file_invalid(self):
        """Test validation with invalid file."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"not a bam file")
            tmp.flush()

            try:
                result = validate_bam_file(tmp.name)
                assert result is False
            finally:
                os.unlink(tmp.name)

    def test_validate_bam_file_nonexistent(self):
        """Test validation with nonexistent file."""
        result = validate_bam_file("nonexistent.bam")
        assert result is False


class TestCLIBasicFunctionality:
    """Test basic CLI functionality."""

    def test_validate_bam_file_with_mock_sorted_bam(self):
        """Test BAM validation with mocked pysam for a sorted BAM."""
        with (
            patch("os.path.exists") as mock_exists,
            patch("os.path.getmtime") as mock_getmtime,
            patch("pysam.AlignmentFile") as mock_bam,
            patch("pysam.index") as mock_pysam_index,
        ):
            # Mock file existence and timestamps
            mock_exists.side_effect = lambda _: True  # Both BAM and BAI exist
            mock_getmtime.side_effect = lambda x: 1000 if x.endswith(".bam") else 1001 # Index is newer

            # Mock successful BAM file opening and header
            mock_header = {"HD": {"SO": "coordinate"}}
            mock_bam.return_value.__enter__.return_value.header = mock_header
            mock_bam.return_value.__exit__.return_value = None

            result = validate_bam_file("test.bam")
            assert result is True
            mock_pysam_index.assert_not_called() # Index should not be rebuilt

    def test_validate_bam_file_with_mock_unsorted_bam(self):
        """Test BAM validation with mocked pysam for an unsorted BAM."""
        with (
            patch("os.path.exists") as mock_exists,
            patch("os.path.getmtime") as mock_getmtime,
            patch("pysam.AlignmentFile") as mock_bam,
            patch("pysam.index") as mock_pysam_index,
        ):
            # Mock file existence and timestamps
            mock_exists.side_effect = lambda _: True
            mock_getmtime.return_value = 1000

            # Mock unsorted BAM header
            mock_header = {"HD": {"SO": "queryname"}}
            mock_bam.return_value.__enter__.return_value.header = mock_header
            mock_bam.return_value.__exit__.return_value = None

            result = validate_bam_file("test.bam")
            assert result is False
            mock_pysam_index.assert_not_called()

    def test_validate_bam_file_with_mock_old_index(self):
        """Test BAM validation with mocked pysam for an old index."""
        with (
            patch("os.path.exists") as mock_exists,
            patch("os.path.getmtime") as mock_getmtime,
            patch("pysam.AlignmentFile") as mock_bam,
            patch("pysam.index") as mock_pysam_index,
        ):
            # Mock file existence and timestamps (index older than bam)
            mock_exists.side_effect = lambda _: True
            mock_getmtime.side_effect = lambda x: 1000 if x.endswith(".bam") else 999

            # Mock successful BAM file opening and header
            mock_header = {"HD": {"SO": "coordinate"}}
            mock_bam.return_value.__enter__.return_value.header = mock_header
            mock_bam.return_value.__exit__.return_value = None

            result = validate_bam_file("test.bam")
            assert result is True
            mock_pysam_index.assert_called_once_with("test.bam", "-@", "1")

    def test_validate_bam_file_with_mock_no_index(self):
        """Test BAM validation with mocked pysam for no index."""
        with (
            patch("os.path.exists") as mock_exists,
            patch("os.path.getmtime") as mock_getmtime,
            patch("pysam.AlignmentFile") as mock_bam,
            patch("pysam.index") as mock_pysam_index,
        ):
            # Mock file existence (BAM exists, BAI does not)
            mock_exists.side_effect = lambda x: not x.endswith(".bai")
            mock_getmtime.return_value = 1000

            # Mock successful BAM file opening and header
            mock_header = {"HD": {"SO": "coordinate"}}
            mock_bam.return_value.__enter__.return_value.header = mock_header
            mock_bam.return_value.__exit__.return_value = None

            result = validate_bam_file("test.bam")
            assert result is True
            mock_pysam_index.assert_called_once_with("test.bam", "-@", "1")

    def test_validate_sam_file_with_mock(self):
        """Test SAM validation with mocked pysam."""
        with (
            patch("os.path.exists") as mock_exists,
            patch("pysam.AlignmentFile") as mock_sam,
        ):
            mock_exists.return_value = True
            mock_header = {"HD": {"SO": "coordinate"}}
            mock_sam.return_value.__enter__.return_value.header = mock_header
            mock_sam.return_value.__exit__.return_value = None

            result = validate_bam_file("test.sam")
            assert result is True

    def test_validate_bam_file_with_mock_error(self):
        """Test BAM validation with mocked pysam error."""
        with patch("pysam.AlignmentFile") as mock_bam:
            # Mock BAM file opening error
            mock_bam.side_effect = Exception("BAM file error")

            result = validate_bam_file("test.bam")
            assert result is False


    def test_cli_mark_fragment_option(self):
        """Test the --mark-fragment CLI option."""
        import pysam
        from click.testing import CliRunner

        from markdup.cli import main

        runner = CliRunner()

        tmp_input_bam = tempfile.NamedTemporaryFile(suffix=".bam", delete=False)
        tmp_output_bam = tempfile.NamedTemporaryFile(suffix=".bam", delete=False)
        input_bam_path = tmp_input_bam.name
        output_bam_path = tmp_output_bam.name
        tmp_input_bam.close()
        tmp_output_bam.close()

        try:
            # Create a dummy BAM file for input
            with pysam.AlignmentFile(input_bam_path, "wb", header={'HD': {'VN': '1.0', 'SO': 'coordinate'}, 'SQ': [{'LN': 1000, 'SN': 'chr1'}]}) as f:
                f.write(pysam.AlignedSegment())

            with patch("markdup.cli.process_bam") as mock_process_bam, patch("markdup.cli.validate_bam_file", return_value=True):
                with patch("rich.console.Console.input", return_value="y"): # Auto-confirm overwrite
                    result = runner.invoke(main, ["-i", input_bam_path, "-o", output_bam_path, "--mark-fragment"])

                    assert result.exit_code == 0, f"CLI exited with code {result.exit_code}: {result.output}"
                    mock_process_bam.assert_called_once()
                    # Check that process_bam was called with mark_fragment=True
                    args, kwargs = mock_process_bam.call_args
                    assert kwargs["mark_fragment"] is True
        finally:
            os.unlink(input_bam_path)
            os.unlink(output_bam_path)

    def test_cli_no_mark_fragment_option(self):
        """Test the default behavior when --mark-fragment is not used."""
        import pysam
        from click.testing import CliRunner

        from markdup.cli import main

        runner = CliRunner()

        tmp_input_bam = tempfile.NamedTemporaryFile(suffix=".bam", delete=False)
        tmp_output_bam = tempfile.NamedTemporaryFile(suffix=".bam", delete=False)
        input_bam_path = tmp_input_bam.name
        output_bam_path = tmp_output_bam.name
        tmp_input_bam.close()
        tmp_output_bam.close()

        try:
            # Create a dummy BAM file for input
            with pysam.AlignmentFile(input_bam_path, "wb", header={'HD': {'VN': '1.0', 'SO': 'coordinate'}, 'SQ': [{'LN': 1000, 'SN': 'chr1'}]}) as f:
                f.write(pysam.AlignedSegment())

            with patch("markdup.cli.process_bam") as mock_process_bam, patch("markdup.cli.validate_bam_file", return_value=True):
                with patch("rich.console.Console.input", return_value="y"): # Auto-confirm overwrite
                    result = runner.invoke(main, ["-i", input_bam_path, "-o", output_bam_path])

                    assert result.exit_code == 0, f"CLI exited with code {result.exit_code}: {result.output}"
                    mock_process_bam.assert_called_once()
                    # Check that process_bam was called with mark_fragment=False (default)
                    args, kwargs = mock_process_bam.call_args
                    assert kwargs["mark_fragment"] is False
        finally:
            os.unlink(input_bam_path)
            os.unlink(output_bam_path)

if __name__ == "__main__":
    pytest.main([__file__])
