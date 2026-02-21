"""
Tests for lib.validators module.
"""

from datetime import datetime

import pytest

from lib import Note, Task, validate_notes, assert_valid


class TestValidateNotes:
    """Tests for validate_notes function."""
    
    def test_valid_notes(self):
        """Test validation of valid notes."""
        notes = [
            Note(
                id="note-001",
                title="Valid Note",
                content="Content",
                path="Valid Note.md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
        ]
        
        errors = validate_notes(notes)
        assert errors == []
    
    def test_missing_id(self):
        """Test detection of missing note ID."""
        notes = [
            Note(
                id="",
                title="No ID",
                content="Content",
                path="No ID.md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
        ]
        
        errors = validate_notes(notes)
        assert any("Missing id" in e for e in errors)
    
    def test_missing_title(self):
        """Test detection of missing note title."""
        notes = [
            Note(
                id="note-001",
                title="",
                content="Content",
                path=".md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
        ]
        
        errors = validate_notes(notes)
        assert any("Missing title" in e for e in errors)
    
    def test_duplicate_id(self):
        """Test detection of duplicate note IDs."""
        notes = [
            Note(
                id="duplicate",
                title="First",
                content="Content",
                path="First.md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
            Note(
                id="duplicate",
                title="Second",
                content="Content",
                path="Second.md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
        ]
        
        errors = validate_notes(notes)
        assert any("Duplicate id" in e for e in errors)
    
    def test_duplicate_path(self):
        """Test detection of duplicate paths."""
        notes = [
            Note(
                id="note-001",
                title="First",
                content="Content",
                path="Same Path.md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
            Note(
                id="note-002",
                title="Second",
                content="Content",
                path="Same Path.md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
        ]
        
        errors = validate_notes(notes)
        assert any("Duplicate path" in e for e in errors)
    
    def test_task_missing_id(self):
        """Test detection of tasks with missing IDs."""
        notes = [
            Note(
                id="note-001",
                title="Note with Task",
                content="Content",
                path="Note.md",
                created=datetime.now(),
                modified=datetime.now(),
                tasks=[
                    Task(id="", content="Task without ID"),
                ],
            ),
        ]
        
        errors = validate_notes(notes)
        assert any("Task" in e and "missing id" in e for e in errors)


class TestAssertValid:
    """Tests for assert_valid function."""
    
    def test_valid_notes_pass(self):
        """Test that valid notes don't raise an error."""
        notes = [
            Note(
                id="note-001",
                title="Valid",
                content="Content",
                path="Valid.md",
                created=datetime.now(),
                modified=datetime.now(),
            ),
        ]
        
        # Should not raise
        assert_valid(notes)
    
    def test_invalid_notes_raise(self):
        """Test that invalid notes raise ValueError."""
        notes = [
            Note(
                id="",
                title="",
                content="Content",
                path="",
                created=datetime.now(),
                modified=datetime.now(),
            ),
        ]
        
        with pytest.raises(ValueError) as exc_info:
            assert_valid(notes)
        
        assert "Validation failed" in str(exc_info.value)
