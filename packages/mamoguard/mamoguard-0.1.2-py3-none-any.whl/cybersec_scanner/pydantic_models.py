"""
File with different pdantic schemas needed for the models output

"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class Finding(BaseModel):
    commit_hash: str = Field(description="The Git commit SHA hash where this vulnerability was found")
    file_path: str = Field(description="Relative path to the file containing the vulnerability (e.g., 'src/api/auth.py')")
    line_number: Optional[int] = Field(default=None, description="The line number where the vulnerability exists, or None if it spans multiple lines")
    snippet: str = Field(description="The actual vulnerable code snippet extracted from the diff (keep it concise, 1-5 lines)")
    finding_type: str = Field(description="The specific CWE or vulnerability type. Format: 'CWE-XXX: Description'. Examples: 'CWE-89: SQL Injection', 'CWE-79: XSS'")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score: 0.9-1.0 for HIGH confidence that vulnerability exists, 0.6-0.9 for MEDIUM, below 0.6 for LOW")
    rationale: str = Field(description="Brief explanation (2-3 sentences): what's vulnerable, why it's risky, how it could be exploited")
    commit_message: str = Field(default="", description="The commit message associated with this change")
    commit_url: str = Field(default="", description="URL to view this commit in the repository")
    recommendation: Optional[str] = Field(default=None, description="How to fix it in 1-2 sentences")

class FindingsList(BaseModel):
    """Structured output for LLM secret detection"""
    findings: List[Finding] = Field(default_factory=list)