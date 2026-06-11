import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RawJob:
    title: str
    company: str
    url: str
    description: str = ""
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    tech_stack: Optional[list[str]] = None
    employment_type: Optional[str] = None
    source_id: Optional[str] = None
    is_remote: bool = True
    country: Optional[str] = None


def get_dedup_hash(title: str, company: str) -> str:
    normalized = f"{re.sub(r'[^a-z0-9]', '', title.lower())}{re.sub(r'[^a-z0-9]', '', company.lower())}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:64]


class JobSource(ABC):
    source_name: str = "unknown"

    @abstractmethod
    async def fetch(self) -> list[RawJob]:
        ...

    def get_dedup_hash(self, title: str, company: str) -> str:
        return get_dedup_hash(title, company)
