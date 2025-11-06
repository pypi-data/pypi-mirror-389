
# CyberSec Scanner 🔐

The idea of this tool is very simple, iterate over diffs in a commit, look for vulnerability, report it. I thought that it would been useful to have different kinds of analysis that look out for different kind of cybersec issues(injection, broken access control etc). In order to look for issues that actually matter, i found this report https://owasp.org/www-project-top-ten/ that describes top ten cybersec that occur most often. Then I built an analyzer for every group i had time to cover. Secret_analyzer (API keys etc )also has a heuristic analysator just to not miss anything

Keep in mind that it is more of prototype, i have noticed that the tool tends to overestimate how dangerous something is, in my opinion thats good, because it is better to check something that is secure than not check something that is insecure. I can imagine though, that dont want faslo positives and then prompts need tweaking etc. Also probably using OpenAI models can be not very secure, so that can also be improved.


### Right now it covers following groups of cybersec issues
1. Security misconfiguration
2. Broken access
3. Injections
4. Insecure design
5. Secret detection 

Since the logic is identical for every analyser it is very easy to add new kind of analyzers (basically just requires a good prompt)

## Project Overview

```
cybersec_scanner/
├── scanner.py              # Git repository scanner
├── base_analyzer.py        # Base class for analyzers
├── secret_analyzer.py      # Secret detection logic
├── broken_access_analyzer.py # Broken Access control detection
├── injection_analyzer.py   # Injection vulnerability detection
├── design_analyzer.py      # Insecure design vulnerability detection
├── security_misconfig_analyzer.py   # Security misconfiguration vulnerability detection
├── prompts.py              # LLM prompt templates
├── cli.py                  # CLI interface
├── __init__.py
```

- CLI entry point: `mamoguard` (see `setup.py`)
- Each analyzer implements its own logic and prompt
- LLM integration via LangChain and OpenAI
- Output: JSON report with findings per analyzer

## Installation
I have incorporated 2 options for installation: pip from pypi and pip from the repo

1. pip install mamoguard

2. git clone https://github.com/marinamomina/cybersec_scan.git
cd cybersec_scanner
pip install -e .

## Usage
1. This cli is using openai models, so you need to make sure that you have a working open ai api key in your enviroment, if you need one you can ping me

2. Run using cli commands:




## Usage

```bash
mamoguard --repo <path_or_url> [options]
```

## Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--repo` | | *required* | Repository path or URL |
| `--n` | | `10` | Number of commits to scan |
| `--branch` | | `HEAD` | Branch to scan |
| `--out` | | `report.json` | Output JSON file |
| `--analyzers` | `-a` | `all` | Analyzers to run (repeatable) |

## Available Analyzers

- `secrets` - Hardcoded secrets (API keys, passwords, tokens)
- `access` - Broken access control vulnerabilities (OWASP A01)
- `injection` - Injection vulnerabilities: SQL, XSS, Command Injection (OWASP A03)
- `design` - Insecure design patterns
- `secmisconfig` - Security misconfigurations
- `all` - Run all analyzers (default)

## Examples

```bash
mamoguard --n 2 --repo https://github.com/WebGoat/WebGoat -a secmisconfig
```

I really like this repo because it has good examples of insecure design. 

## Output Format

The scanner generates a JSON report with the following structure:

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "repo": "./my-repo",
  "commits_scanned": 10,
  "analyzers_run": ["secrets", "broken_access", "injection"],
  "total_findings": 5,
  "findings": {
    "secrets": [
      {
        "commit_hash": "abc123def456",
        "file_path": "src/config.py",
        "line_number": 42,
        "snippet": "API_KEY = 'sk_live_1234567890'",
        "finding_type": "CWE-798: Hardcoded Credentials",
        "severity": "HIGH",
        "confidence": 0.95,
        "rationale": "Hardcoded API key found in source code. This could be extracted by anyone with repository access.",
        "recommendation": "Use environment variables or secret management service instead of hardcoding credentials.",
        "commit_message": "Add API configuration",
        "commit_url": "https://github.com/user/repo/commit/abc123"
      }
    ],
    "injection": [
      {
        "commit_hash": "def456ghi789",
        "file_path": "api/users.py",
        "line_number": 78,
        "snippet": "query = 'SELECT * FROM users WHERE id=' + user_id",
        "finding_type": "CWE-89: SQL Injection",
        "severity": "HIGH",
        "confidence": 0.92,
        "rationale": "User input concatenated directly into SQL query without parameterization. Attacker can inject malicious SQL.",
        "recommendation": "Use parameterized queries or prepared statements instead of string concatenation.",
        "commit_message": "Add user lookup endpoint",
        "commit_url": "https://github.com/user/repo/commit/def456"
      }
    ]
  }
}
```



## Finding Fields

Each finding contains:

- `commit_hash` - Git commit SHA where vulnerability was introduced
- `file_path` - Relative path to vulnerable file
- `line_number` - Line number of vulnerability (null if spans multiple lines)
- `snippet` - Vulnerable code excerpt (1-5 lines)
- `finding_type` - CWE classification (e.g., "CWE-89: SQL Injection")
- `severity` - Risk level: `HIGH`, `MEDIUM`, or `LOW`
- `confidence` - Detection confidence score (0.0-1.0)
- `rationale` - Explanation of why it's vulnerable and potential impact
- `recommendation` - How to fix the vulnerability
- `commit_message` - Original commit message
- `commit_url` - Link to view commit in repository


## Troubleshooting

### API Key Not Found
```bash
Error: OPENAI_API_KEY not set in .env
```
**Solution**: Create `.env` file with `OPENAI_API_KEY=your-key`

### Repository Not Found
```bash
Error: Repository path does not exist
```
**Solution**: Verify repository path is correct or URL is accessible

### No Findings
If scanner finds 0 vulnerabilities, either:
- LLM didn't detect issues (try different commits/branches)
- Analyzers need tuning for your codebase

#### Running stuff when developing
python cli.py --repo https://github.com/WebGoat/WebGoat  --n 5 -a secmisconfig

#### Push to pypi
rm -rf dist/ build/ *.egg-info
python -m build
twine upload dist/*
