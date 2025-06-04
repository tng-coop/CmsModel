"""Generate in-memory office information for churches."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class OfficeInfo:
    address: str
    phone: str


def generate_office_info(num_churches: int = 50) -> Dict[str, OfficeInfo]:
    """Return a dictionary of sample office info keyed by church id."""
    info: Dict[str, OfficeInfo] = {}
    for i in range(1, num_churches + 1):
        church_id = f"church{i:02d}"
        address = "123 Example St. City, ST"
        phone = f"555-01{i:02d}"
        info[church_id] = OfficeInfo(address=address, phone=phone)
    return info
