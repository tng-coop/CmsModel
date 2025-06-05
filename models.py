from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Category:
    """Represents a content category."""

    name: str
    parent: Optional[str] = None
    sort_order_index: int = 0


@dataclass
class Article:
    """Represents an article item."""

    name: str
    categories: List[str]
    archived: bool = False
