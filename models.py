from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict
from datetime import datetime

class Grant(BaseModel):
    funder: Optional[str] = None
    funder_id: Optional[str] = None
    award_id: Optional[str] = None
    award_amount: Optional[float] = None

class Author(BaseModel):
    author_position: str
    raw_author_name: str
    author_id: Optional[str] = None

class Work(BaseModel):
    id: str
    doi: Optional[str] = None
    title: str
    publication_year: Optional[int] = None
    publication_date: Optional[datetime] = None
    cited_by_count: int
    grants: List[Grant] = []
    authors: List[Author] = []
    abstract: Optional[str] = None
    keywords: List[str] = []
    primary_location: Optional[Dict] = None

class Funder(BaseModel):
    id: str
    display_name: str
    alternate_titles: List[str] = []
    country_code: Optional[str] = None
    description: Optional[str] = None
    homepage_url: Optional[HttpUrl] = None
    image_url: Optional[HttpUrl] = None
    works_count: int
    cited_by_count: int
    grants_count: Optional[int] = None

class ProjectDescription(BaseModel):
    description: str
    max_results: int = 50  # Allow customizing result size

class FundingData(BaseModel):
    funder_name: str
    funder_id: str
    award_id: Optional[str] = None
    award_amount: Optional[float] = None
    paper_title: str
    paper_doi: str

class WorkData(BaseModel):
    title: str
    grants: list
    doi: str
    cited_by_count: int
    publication_year: int 