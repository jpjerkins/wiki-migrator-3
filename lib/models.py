"""
Data models for Wiki Migrator 3.

Uses Pydantic for validation and JSON serialization.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


class Attachment(BaseModel):
    """Represents a file attachment in a note."""
    
    filename: str
    content_type: str = "application/octet-stream"
    data: Optional[bytes] = None
    path: Optional[str] = None  # Relative path if stored separately


class Task(BaseModel):
    """Represents a task within a note."""
    
    id: str
    content: str
    completed: bool = False
    due_date: Optional[datetime] = None
    priority: Optional[str] = None  # e.g., "high", "medium", "low"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Note(BaseModel):
    """Represents a wiki note."""
    
    id: str
    title: str
    content: str
    path: str  # File path in output
    created: datetime
    modified: datetime
    tags: list[str] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    def model_post_init(self, __context) -> None:
        """Ensure tags is always a list."""
        if self.tags is None:
            self.tags = []
        if self.tasks is None:
            self.tasks = []
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}
