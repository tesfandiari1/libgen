from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BookInfo(BaseModel):
    md5: str
    title: str
    author: Optional[str] = None
    year: Optional[int] = Field(default=None, ge=0)
    pages: Optional[int] = Field(default=None, ge=1)
    file_format: Optional[str] = None
    filesize: Optional[str] = None


class SearchIntent(BaseModel):
    query: str
    min_year: Optional[int] = Field(default=None, ge=0)
    formats: Optional[List[str]] = None
    max_results: int = Field(default=25, ge=1, le=200)


