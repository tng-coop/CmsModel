from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """Represents a content category."""

    name: str
    parent: Optional[str] = None


@dataclass
class Content:
    """Represents a content item."""

    name: str
    content_type: str
    category: str
    action: str
