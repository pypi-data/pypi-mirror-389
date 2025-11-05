from git import Repo
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
import tempfile
import shutil
from pathlib import Path


class Author(BaseModel):
    name: str
    email: str


class DiffItem(BaseModel):
    a_path: Optional[str]  # Old file path
    b_path: Optional[str]  # New file path
    diff: str  # The actual diff content
    change_type: Optional[Literal['A', 'M', 'D', 'R', 'T']] = None  # Added Optional and 'T' for type change idk why some of them are nonoe
    new_file: bool
    deleted_file: bool
    renamed: bool


class Commit(BaseModel):
    hexsha: str
    message: str
    author: Author
    authored_date: datetime
    committer: Author
    diffs: List[DiffItem] = Field(default_factory=list)
    stats_files_changed: int = 0
    stats_insertions: int = 0
    stats_deletions: int = 0


class GitRepoScanner:
    def __init__(self, repo_url: str, n_commits: int, branch: str = 'HEAD'):
        """
        Initialize scanner with repo URL and number of commits to scan.
        
        Args:
            repo_url: GitHub repo URL (https://github.com/user/repo.git) or local path
            n_commits: Number of most recent commits to scan
            branch: Branch to scan (default: 'HEAD')
        """
        self.repo_url = repo_url
        self.n_commits = n_commits
        self.branch = branch
        self.temp_dir = None
        self.commits: List[Commit] = []

    def scan(self) -> List[Commit]:
        """
        Scan the repository and extract all commit data.
        Automatically cleans up temp directory after scanning.
        
        Returns:
            List of Commit objects with full data
        """
        try:
            # Load repository
            repo = self._load_repo()
            
            # Get last N commits from specified branch
            commit_list = list(repo.iter_commits(self.branch, max_count=self.n_commits))
            
            # Extract data from each commit
            for git_commit in commit_list:
                commit_data = self._extract_commit_data(git_commit)
                self.commits.append(commit_data)
            
            return self.commits
        
        finally:
            # Always cleanup temp directory
            self._cleanup()
    
    def _load_repo(self) -> Repo:
        """Load repository from URL or local path."""
        # Check if it's a local path
        if Path(self.repo_url).is_dir():
            return Repo(self.repo_url)
        
        # Otherwise, clone from remote URL
        self.temp_dir = tempfile.mkdtemp()
        return Repo.clone_from(
            self.repo_url,
            self.temp_dir,
            #depth=self.n_commits  # Shallow clone for efficiency
        )
    
    def _extract_commit_data(self, git_commit) -> Commit:
        """Extract all data from a git commit object."""
        # Extract author
        author = Author(
            name=git_commit.author.name,
            email=git_commit.author.email
        )
        
        # Extract committer
        committer = Author(
            name=git_commit.committer.name,
            email=git_commit.committer.email
        )
        
        # Extract diffs
        diffs = []
        if git_commit.parents:
            diff_index = git_commit.parents[0].diff(git_commit, create_patch=True)
            for diff_item in diff_index:
                try:
                    diff_content = diff_item.diff.decode('utf-8') if diff_item.diff else ""
                except UnicodeDecodeError:
                    # Skip binary files
                    diff_content = "[Binary file]"
                
                diffs.append(DiffItem(
                    a_path=diff_item.a_path,
                    b_path=diff_item.b_path,
                    diff=diff_content,
                    change_type=diff_item.change_type,
                    new_file=diff_item.new_file,
                    deleted_file=diff_item.deleted_file,
                    renamed=diff_item.renamed
                ))
        
        # Extract stats
        stats = git_commit.stats.total
        
        # Create Commit object
        return Commit(
            hexsha=git_commit.hexsha,
            message=git_commit.message,
            author=author,
            authored_date=datetime.fromtimestamp(git_commit.authored_date),
            committer=committer,
            diffs=diffs,
            stats_files_changed=stats.get('files', 0),
            stats_insertions=stats.get('insertions', 0),
            stats_deletions=stats.get('deletions', 0)
        )
    
    def _cleanup(self):
        """Remove temporary directory if it was created."""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None


# Usage example:
if __name__ == "__main__":
    scanner = GitRepoScanner(
        repo_url="https://github.com/uncletoxa/ulauncher-jetbrains",
        branch='master',
        n_commits=8
    )
    
    commits = scanner.scan()
    
    # Now you have all commit data in Pydantic models
    for commit in commits:
        print(f"Commit: {commit.hexsha[:8]}")
        print(f"Message: {commit.message}")
        print(f"Author: {commit.author.name} <{commit.author.email}>")
        print(f"Files changed: {commit.stats_files_changed}")
        print(f"Diffs: {len(commit.diffs)}")
