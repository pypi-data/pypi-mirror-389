"""
File with different pdantic schemas needed for the models output

"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class Finding(BaseModel):
    commit_hash: str
    file_path: str
    line_number: Optional[int]
    snippet: str
    finding_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    commit_message: str = ""  
    commit_url: str = ""      

class FindingsList(BaseModel):
    """Structured output for LLM secret detection"""
    findings: List[Finding] = Field(default_factory=list)