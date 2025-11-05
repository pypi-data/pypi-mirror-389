from abc import ABC, abstractmethod
from typing import List, TypeVar, Generic
from pydantic import BaseModel
import re
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

# Generic type for findings - each analyzer can define its own
FindingType = TypeVar('FindingType', bound=BaseModel)

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

class DiffItem(BaseModel):
    """Represents a single diff in a commit"""
    diff: str = Field(description="The actual diff content")
    a_path: Optional[str] = Field(None, description="Path in old version (deleted/modified files)")
    b_path: Optional[str] = Field(None, description="Path in new version (added/modified files)")


class Commit(BaseModel):
    """Represents a git commit with its diffs"""
    hexsha: str = Field(description="Commit hash (SHA)")
    message: str = Field(description="Commit message")
    diffs: List[DiffItem] = Field(default_factory=list, description="List of diffs in this commit")



class BaseAnalyzer(ABC, Generic[FindingType]):
    """Base class for all vulnerability analyzers"""
    
    def __init__(self, repo_url: str):
        self.repo_url = repo_url
    
    def analyze(self, commits: List['Commit']) -> List[FindingType]:
        """Main entry point - orchestrates the analysis"""
        all_findings = []
        
        for commit in commits:
            # Common iteration logic
            for diff_item in commit.diffs:
                if self._should_skip_diff(diff_item):
                    continue
                
                file_path = diff_item.b_path or diff_item.a_path or 'unknown'
                
                # Call analyzer-specific logic
                findings = self._analyze_diff(
                    commit=commit,
                    diff_item=diff_item,
                    file_path=file_path
                )
                
                all_findings.extend(findings)
        
        # Enrich all findings with commit metadata
        return self._enrich_findings(all_findings, commits)
    
    def _should_skip_diff(self, diff_item) -> bool:
        """Common logic to skip binary/empty diffs"""
        return (diff_item.diff == "[Binary file]" or 
                not diff_item.diff or 
                len(diff_item.diff.strip()) == 0)
    
    @abstractmethod
    def _analyze_diff(self, commit, diff_item, file_path: str) -> List[FindingType]:
        """Analyzer-specific logic - must be implemented by subclasses"""
        pass
    
    def _enrich_findings(self, findings: List[FindingType], 
                        commits: List['Commit']) -> List[FindingType]:
        """Add commit metadata to findings"""
        commit_map = {commit.hexsha: commit for commit in commits}
        
        for finding in findings:
            commit = commit_map.get(finding.commit_hash)
            if commit and hasattr(finding, 'commit_message'):
                finding.commit_message = commit.message
                finding.commit_url = f"{self.repo_url}/commit/{commit.hexsha}"
        
        return findings
    
    def _parse_added_lines(self, diff_content: str) -> List[tuple[int, str]]:
        """Common utility - parse diff for added lines"""
        lines_with_numbers = []
        lines = diff_content.split('\n')
        current_line_num = 0
        
        for line in lines:
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line_num = int(match.group(1))
                continue
            
            if line.startswith('+') and not line.startswith('+++'):
                actual_content = line[1:]
                lines_with_numbers.append((current_line_num, actual_content))
                current_line_num += 1
            elif not line.startswith('-'):
                current_line_num += 1
        
        return lines_with_numbers