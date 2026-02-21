"""
Tests for lib.models module.
"""

from datetime import datetime

import pytest

from lib import Note, Task, Attachment


class TestNote:
    """Tests for the Note model."""
    
    def test_note_creation(self):
        """Test creating a basic Note."""
        note = Note(
            id="test-001",
            title="Test Note",
            content="Test content",
            path="Test Note.md",
            created=datetime.now(),
            modified=datetime.now(),
        )
        
        assert note.id == "test-001"
        assert note.title == "Test Note"
        assert note.tags == []
        assert note.tasks == []
    
    def test_note_with_tags(self):
        """Test creating a Note with tags."""
        note = Note(
            id="test-002",
            title="Tagged Note",
            content="Content",
            path="Tagged Note.md",
            created=datetime.now(),
            modified=datetime.now(),
            tags=["important", "work"],
        )
        
        assert "important" in note.tags
        assert "work" in note.tags
    
    def test_note_json_serialization(self):
        """Test Note serialization to JSON."""
        note = Note(
            id="test-003",
            title="JSON Test",
            content="Test",
            path="JSON Test.md",
            created=datetime(2024, 1, 1, 12, 0, 0),
            modified=datetime(2024, 1, 1, 12, 0, 0),
            tags=["test"],
        )
        
        data = note.model_dump(mode="json")
        
        assert data["id"] == "test-003"
        assert data["title"] == "JSON Test"
        assert "test" in data["tags"]


class TestTask:
    """Tests for the Task model."""
    
    def test_task_creation(self):
        """Test creating a Task."""
        task = Task(
            id="task-001",
            content="Complete this task",
            completed=False,
        )
        
        assert task.id == "task-001"
        assert task.content == "Complete this task"
        assert task.completed is False
    
    def test_task_with_priority(self):
        """Test creating a Task with priority."""
        task = Task(
            id="task-002",
            content="High priority task",
            completed=False,
            priority="high",
        )
        
        assert task.priority == "high"


class TestAttachment:
    """Tests for the Attachment model."""
    
    def test_attachment_creation(self):
        """Test creating an Attachment."""
        att = Attachment(
            filename="image.png",
            content_type="image/png",
            path="attachments/image.png",
        )
        
        assert att.filename == "image.png"
        assert att.content_type == "image/png"
