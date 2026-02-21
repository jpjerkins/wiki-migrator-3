"""
Pytest configuration and fixtures.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

# Add lib to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import Note, Task, Attachment


@pytest.fixture
def sample_note() -> Note:
    """Return a sample Note for testing."""
    return Note(
        id="test-001",
        title="Test Note",
        content="# Test Note\n\nThis is a test.",
        path="Test Note.md",
        created=datetime(2024, 1, 1, 12, 0, 0),
        modified=datetime(2024, 1, 1, 12, 0, 0),
        tags=["test", "sample"],
        tasks=[],
        attachments=[],
        metadata={"source": "test"},
    )


@pytest.fixture
def sample_notes() -> list[Note]:
    """Return a list of sample Notes for testing."""
    return [
        Note(
            id="test-001",
            title="First Note",
            content="Content of first note.",
            path="First Note.md",
            created=datetime(2024, 1, 1, 12, 0, 0),
            modified=datetime(2024, 1, 1, 12, 0, 0),
            tags=["test"],
        ),
        Note(
            id="test-002",
            title="Second Note",
            content="Content of second note.",
            path="folder/Second Note.md",
            created=datetime(2024, 1, 2, 12, 0, 0),
            modified=datetime(2024, 1, 2, 12, 0, 0),
            tags=[],
            tasks=[
                Task(id="task-001", content="Do something", completed=False),
                Task(id="task-002", content="Do another thing", completed=True),
            ],
        ),
    ]


@pytest.fixture
def temp_output_dir():
    """Provide a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
