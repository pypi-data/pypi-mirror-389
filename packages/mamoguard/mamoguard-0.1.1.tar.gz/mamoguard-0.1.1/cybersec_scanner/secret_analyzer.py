from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import re
from datetime import datetime
from langchain_openai import ChatOpenAI
from .prompts import secrets_prompt
from .pydantic_models import FindingsList, Finding


load_dotenv()


class HeuristicAnalyzer:
    # Regex patterns for common secrets
    PATTERNS = {
        'aws_access_key': (
            r'AKIA[0-9A-Z]{16}',
            0.9,
            'AWS Access Key ID format'
        ),
        'aws_secret_key': (
            r'(?i)aws(.{0,20})?[\'\"][0-9a-zA-Z\/+]{40}[\'\"]',
            0.8,
            'AWS Secret Access Key pattern'
        ),
        'github_token': (
            r'ghp_[0-9a-zA-Z]{36}',
            0.95,
            'GitHub Personal Access Token'
        ),
        'github_oauth': (
            r'gho_[0-9a-zA-Z]{36}',
            0.95,
            'GitHub OAuth Token'
        ),
        'generic_api_key': (
            r'(?i)(api[_-]?key|apikey)[\s]*[=:]+[\s]*[\'\"]([a-zA-Z0-9_\-]{20,})[\'\"]',
            0.7,
            'Generic API key pattern'
        ),
        'password_assignment': (
            r'(?i)(password|passwd|pwd)[\s]*[=:]+[\s]*[\'\"]([^\'\"\s]{4,})[\'\"]',
            0.6,
            'Hardcoded password'
        ),
        'private_key': (
            r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            0.95,
            'Private key detected'
        ),
        'slack_token': (
            r'xox[baprs]-[0-9a-zA-Z]{10,}',
            0.9,
            'Slack token format'
        ),
        'stripe_key': (
            r'(?:sk|pk)_(test|live)_[0-9a-zA-Z]{24,}',
            0.9,
            'Stripe API key'
        ),
        'jwt_token': (
            r'eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}',
            0.75,
            'JWT token pattern'
        ),
        'connection_string': (
            r'(?i)(mongodb|postgres|mysql):\/\/[^\s\'"]+:[^\s\'"]+@[^\s\'"]+',
            0.85,
            'Database connection string with credentials'
        ),
    }
    
    def scan(self, commits: List['Commit']) -> List[Finding]:
        """Scan commits using heuristic patterns."""
        findings = []
        
        for commit in commits:
            # Check commit message for secrets
            findings.extend(self._scan_text(
                commit.message,
                commit.hexsha,
                'commit_message',
                None
            ))
            
            # Check diffs
            for diff_item in commit.diffs:
                if diff_item.diff == "[Binary file]":
                    continue
                
                file_path = diff_item.b_path or diff_item.a_path or 'unknown'
                findings.extend(self._scan_diff(
                    diff_item.diff,
                    commit.hexsha,
                    file_path
                ))
        
        return findings
    
    def _scan_diff(self, diff_content: str, commit_hash: str, file_path: str) -> List[Finding]:
        """Scan diff content for secrets."""
        findings = []
        
        # Parse diff to get added lines
        lines = diff_content.split('\n')
        line_number = 0
        
        for line in lines:
            # Track line numbers in new file
            if line.startswith('@@'):
                # Parse hunk header: @@ -old_start,old_count +new_start,new_count @@
                match = re.search(r'\+(\d+)', line)
                if match:
                    line_number = int(match.group(1))
                continue
            
            # Only scan added lines (starting with +)
            if line.startswith('+') and not line.startswith('+++'):
                actual_line = line[1:]  # Remove the '+' prefix
                findings.extend(self._scan_text(
                    actual_line,
                    commit_hash,
                    file_path,
                    line_number
                ))
                line_number += 1
            elif not line.startswith('-'):
                line_number += 1
        
        return findings
    
    def _scan_text(self, text: str, commit_hash: str, file_path: str, 
                   line_number: Optional[int]) -> List[Finding]:
        """Scan text for patterns."""
        findings = []
        
        for finding_type, (pattern, confidence, rationale) in self.PATTERNS.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                # Create snippet with context
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                snippet = text[start:end].strip()
                
                # Truncate if too long
                if len(snippet) > 100:
                    snippet = snippet[:97] + '...'
                
                findings.append(Finding(
                    commit_hash=commit_hash,
                    file_path=file_path,
                    line_number=line_number,
                    snippet=snippet,
                    finding_type=finding_type,
                    confidence=confidence,
                    rationale=rationale
                ))
        
        # Check for high entropy strings (potential secrets)
        entropy_findings = self._check_entropy(text, commit_hash, file_path, line_number)
        findings.extend(entropy_findings)
        
        return findings
    
    def _check_entropy(self, text: str, commit_hash: str, file_path: str,
                       line_number: Optional[int]) -> List[Finding]:
        """Check for high entropy strings."""
        findings = []
        
        # Look for quoted strings with high entropy
        quoted_strings = re.findall(r'["\']([a-zA-Z0-9+/=_-]{20,})["\']', text)
        
        for string in quoted_strings:
            entropy = self._calculate_entropy(string)
            
            # High entropy threshold (likely random/encoded)
            if entropy > 4.5 and len(string) >= 20:
                snippet = text[max(0, text.find(string) - 20):
                              min(len(text), text.find(string) + len(string) + 20)].strip()
                
                if len(snippet) > 100:
                    snippet = snippet[:97] + '...'
                
                findings.append(Finding(
                    commit_hash=commit_hash,
                    file_path=file_path,
                    line_number=line_number,
                    snippet=snippet,
                    finding_type='high_entropy_string',
                    confidence=0.5,
                    rationale=f'High entropy string (entropy: {entropy:.2f})'
                ))
        
        return findings
    
    def _calculate_entropy(self, string: str) -> float:
        """Calculate Shannon entropy of a string."""
        if not string:
            return 0.0
        
        from collections import Counter
        import math
        
        # Count character frequencies
        counts = Counter(string)
        length = len(string)
        
        # Calculate entropy
        entropy = 0.0
        for count in counts.values():
            probability = count / length
            entropy -= probability * math.log2(probability)
        
        return entropy

class LLMAnalyzer:
    def __init__(self, api_key: str, model: str = "gpt-4.1"):
        """Initialize with Gemini API key."""
        self.llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            temperature=0
        ).with_structured_output(FindingsList)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", secrets_prompt),
                        
                        ("human", """Commit: {commit_hash}
            File: {file_path}

            Diff content:
            {diff_content}

            Analyze this diff for real secrets. For each finding, provide:
            - line_number: where secret appears
            - snippet: small context (20-50 chars)
            - finding_type: api_key, password, private_key, token, etc.
            - confidence: 0.0 to 1.0
            - rationale: why this is a real secret

            Only include high confidence findings. over 0.5""")
                    ])
        
        self.chain = self.prompt | self.llm
    
    def _parse_added_lines(self, diff_content: str) -> List[tuple[int, str]]:
        """Parse diff and return list of (line_number, content) for added lines."""
        lines_with_numbers = []
        lines = diff_content.split('\n')
        current_line_num = 0
        
        for line in lines:
            # Parse hunk header to get starting line number
            if line.startswith('@@'):
                match = re.search(r'\+(\d+)', line)
                if match:
                    current_line_num = int(match.group(1))
                continue
            
            # Capture added lines (starting with +)
            if line.startswith('+') and not line.startswith('+++'):
                actual_content = line[1:]  # Remove '+' prefix
                lines_with_numbers.append((current_line_num, actual_content))
                current_line_num += 1
            elif not line.startswith('-'):
                current_line_num += 1
        
        return lines_with_numbers

    def _format_diff_with_line_numbers(self, lines_with_numbers: List[tuple[int, str]]) -> str:
        """Format added lines with explicit line numbers for LLM."""
        formatted = []
        for line_num, content in lines_with_numbers:
            formatted.append(f"Line {line_num}: {content}")
        return '\n'.join(formatted)
    
    def scan(self, commits: List['Commit']) -> List[Finding]:
        """Scan commits using LLM analysis."""
        all_findings = []
        
        for commit in commits:
            for diff_item in commit.diffs:
                if diff_item.diff == "[Binary file]" or not diff_item.diff:
                    continue
                
                file_path = diff_item.b_path or diff_item.a_path or 'unknown'
                
                # Parse diff to extract added lines with line numbers
                added_lines_with_numbers = self._parse_added_lines(diff_item.diff)
                
                if len(added_lines_with_numbers) < 2:
                    continue
                
                try:
                    # Format diff with line numbers for LLM
                    formatted_diff = self._format_diff_with_line_numbers(
                        added_lines_with_numbers
                    )
                    
                    result = self.chain.invoke({
                        "commit_hash": commit.hexsha,
                        "file_path": file_path,
                        "diff_content": formatted_diff
                    })
                    
                    all_findings.extend(result.findings)
                    
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
        
        return all_findings

class SecretAnalyzer:
    """Orchestrates both heuristic and LLM analysis for fiding secrets etc."""
    
    def __init__(self, llm_api_key: str, repo_url: str):
        self.heuristic = HeuristicAnalyzer()
        self.llm_analyzer = LLMAnalyzer(llm_api_key)
        self.repo_url = repo_url

    def _enrich_with_commit_info(self, findings: List[Finding], 
                              commits: List['Commit']) -> List[Finding]:
        """Add commit message and URL to findings after merge."""
        
        # Create lookup map: commit_hash -> commit object
        commit_map = {commit.hexsha: commit for commit in commits}
        
        # Populate commit info for each finding
        for finding in findings:
            commit = commit_map.get(finding.commit_hash)
            if commit:
                finding.commit_message = commit.message
                finding.commit_url = f"{self.repo_url}/commit/{commit.hexsha}"
        
        return findings
    
    def analyze(self, commits: List['Commit']) -> List[Finding]:
        """Run both analyzers and merge results."""
        print("Running heuristic analysis...")
        heuristic_findings = self.heuristic.scan(commits)
        print(f"Heuristic found: {len(heuristic_findings)} findings")
        
        print("\nRunning LLM analysis...")
        llm_findings = self.llm_analyzer.scan(commits)
        print(f"LLM found: {len(llm_findings)} findings")
        
        print("\nMerging results...")
        merged = self._merge_findings(heuristic_findings, llm_findings)
        print(f"Total unique findings: {len(merged)}")

        enriched_findings = self._enrich_with_commit_info(merged, commits)
        
        return enriched_findings
    
    def _merge_findings(self, h_findings: List[Finding], l_findings: List[Finding]) -> List[Finding]:
        """Merge and deduplicate findings from both analyzers."""
        def finding_key(f: Finding) -> tuple:
            return (f.commit_hash, f.file_path, f.line_number, f.snippet[:50])
        
        h_map: Dict[tuple, Finding] = {}
        for finding in h_findings:
            key = finding_key(finding)
            h_map[key] = finding
        
        merged_findings = []
        seen_keys = set()
        
        # Process LLM findings
        for l_finding in l_findings:
            key = finding_key(l_finding)
            
            if key in h_map:
                # Found by both - boost confidence
                h_finding = h_map[key]
                merged_findings.append(Finding(
                    commit_hash=l_finding.commit_hash,
                    file_path=l_finding.file_path,
                    line_number=l_finding.line_number,
                    snippet=l_finding.snippet,
                    finding_type=f"{h_finding.finding_type}+{l_finding.finding_type}",
                    confidence=min(0.95, (h_finding.confidence + l_finding.confidence) / 2 + 0.2),
                    rationale=f"[BOTH] Heuristic: {h_finding.rationale} | LLM: {l_finding.rationale}"
                ))
                seen_keys.add(key)
            else:
                # LLM only
                merged_findings.append(Finding(
                    commit_hash=l_finding.commit_hash,
                    file_path=l_finding.file_path,
                    line_number=l_finding.line_number,
                    snippet=l_finding.snippet,
                    finding_type=f"llm_{l_finding.finding_type}",
                    confidence=l_finding.confidence,
                    rationale=f"[LLM] {l_finding.rationale}"
                ))
                seen_keys.add(key)
        
        # Add heuristic-only findings
        for key, h_finding in h_map.items():
            if key not in seen_keys:
                merged_findings.append(Finding(
                    commit_hash=h_finding.commit_hash,
                    file_path=h_finding.file_path,
                    line_number=h_finding.line_number,
                    snippet=h_finding.snippet,
                    finding_type=f"heuristic_{h_finding.finding_type}",
                    confidence=h_finding.confidence,
                    rationale=f"[HEURISTIC] {h_finding.rationale}"
                ))
        
        merged_findings.sort(key=lambda x: x.confidence, reverse=True)
        return merged_findings


# TEST
if __name__ == "__main__":
    import os
    from cybersec_scanner.scanner import GitRepoScanner
    
    # Get API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY environment variable")
        exit(1)
    
    # 1. Scan repository
    print("="*60)
    print("STEP 1: Scanning repository...")
    print("="*60)
    
    scanner = GitRepoScanner(
        repo_url="https://github.com/uncletoxa/ulauncher-jetbrains",
        branch='master',
        n_commits=5
    )
    
    commits = scanner.scan()
    print(f"Scanned {len(commits)} commits")
    
    # 2. Analyze
    print("\n" + "="*60)
    print("STEP 2: Analyzing for secrets...")
    print("="*60 + "\n")
    
    analyzer = SecretAnalyzer(llm_api_key=api_key)
    findings = analyzer.analyze(commits)
    
    # 3. Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60 + "\n")
    
    if not findings:
        print("✅ No secrets found!")
    else:
        for i, finding in enumerate(findings, 1):
            print(f"{i}. [{finding.confidence:.2f}] {finding.finding_type.upper()}")
            print(f"   Commit: {finding.commit_hash[:8]}")
            print(f"   File: {finding.file_path}:{finding.line_number or 'N/A'}")
            print(f"   Snippet: {finding.snippet}")
            print(f"   {finding.rationale}")
            print()
    
    # 4. Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total findings: {len(findings)}")
    print(f"High confidence (>0.8): {len([f for f in findings if f.confidence > 0.8])}")