"""
Tests for lib.io module.
"""

import json
from datetime import datetime

import pytest

from lib import Note, load_json, save_output
from lib.io import sanitize_filename


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""
    
    def test_basic_filename(self):
        """Test sanitizing a basic filename."""
        assert sanitize_filename("My Note") == "My Note"
    
    def test_invalid_characters(self):
        """Test removing invalid characters."""
        assert sanitize_filename("Note: Test") == "Note_ Test"
        assert sanitize_filename("File/Name") == "File_Name"
        assert sanitize_filename('File"Quote') == "File_Quote"
    
    def test_trailing_periods(self):
        """Test removing trailing periods."""
        assert sanitize_filename("Note.") == "Note"
        assert sanitize_filename("Note...") == "Note"
    
    def test_empty_result(self):
        """Test handling of strings that become empty."""
        assert sanitize_filename(":/<>\\") == "untitled"


class TestLoadJson:
    """Tests for load_json function."""
    
    def test_load_notes(self, temp_output_dir, sample_notes):
        """Test loading notes from JSON."""
        # First save some notes
        save_output(temp_output_dir, sample_notes)
        
        # Then load them back
        loaded = load_json(temp_output_dir)
        
        assert len(loaded) == 2
        assert loaded[0].id == "test-001"
        assert loaded[1].id == "test-002"
    
    def test_load_nonexistent_folder(self):
        """Test loading from a folder that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_json("/nonexistent/path")
    
    def test_load_missing_json(self, temp_output_dir):
        """Test loading from a folder without notes.json."""
        with pytest.raises(FileNotFoundError):
            load_json(temp_output_dir)


class TestSaveOutput:
    """Tests for save_output function."""
    
    def test_save_creates_json(self, temp_output_dir, sample_notes):
        """Test that save_output creates notes.json."""
        save_output(temp_output_dir, sample_notes)
        
        json_path = temp_output_dir / "notes.json"
        assert json_path.exists()
    
    def test_save_creates_markdown(self, temp_output_dir, sample_notes):
        """Test that save_output creates markdown files."""
        save_output(temp_output_dir, sample_notes)
        
        md_path = temp_output_dir / "First Note.md"
        assert md_path.exists()
        
        content = md_path.read_text(encoding="utf-8")
        assert "# First Note" in content
    
    def test_save_nested_paths(self, temp_output_dir, sample_notes):
        """Test saving notes with nested paths."""
        save_output(temp_output_dir, sample_notes)
        
        nested_path = temp_output_dir / "folder" / "Second Note.md"
        assert nested_path.exists()
