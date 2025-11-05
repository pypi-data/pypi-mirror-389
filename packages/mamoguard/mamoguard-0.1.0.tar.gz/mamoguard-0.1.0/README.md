
# CyberSec Scanner 🔐

The idea of this tool is very simple, iterate over diffs in a commit, look for vulnerability, report it. I thought that it would been useful to have different kinds of analysis that look out for different kind of cybersec issues(injection, broken access control etc). In order to look for issues that actually matter, i found this report https://owasp.org/www-project-top-ten/ that describes top ten cybersec  that occur most often. Then i just built an object for every group i could cover. secret_analyzer also has a heuristic analysator just to not miss anything


Right now it covers
1. Secret detection
2. Broken access
3. Injections

How to run 
1. python cli.py --repo https://github.com/WebGoat/WebGoat  --n 5 -a secmisconfig

Ides to explore in the future: 
1. fine tune llm on CWE to have a smaller cheaper local model
2. Maybe it makes sense to run something on the level of the whole codebase, cause diffs do not have the whole context or look at diffs with respect to all db

## Features

- 🔍 **Dual Analysis**: Combines regex-based heuristics with LLM intelligence
- 🧠 **Smart Detection**: Uses Google Gemini to catch context-dependent secrets
- 📊 **Comprehensive Reporting**: Detailed JSON reports with confidence scores
- ⚡ **Fast & Efficient**: Heuristic pre-filtering reduces LLM API costs
- 🎯 **Low False Positives**: Cross-validates findings from both analyzers

## What It Detects

- AWS Access Keys & Secret Keys
- GitHub Personal Access Tokens
- API Keys (Stripe, Slack, generic)
- Private SSH/RSA Keys
- Database Connection Strings
- JWT Tokens
- Hardcoded Passwords
- High-entropy strings (potential secrets)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cybersec-scanner.git
cd cybersec-scanner

# Install dependencies
pip install -r requirements.txt

# Install as CLI tool
pip install -e .
```

## Setup

1. **Get Google Gemini API Key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create an API key

2. **Configure environment**
   ```bash
   # Create .env file
   echo "GEMINI_API_KEY=your-api-key-here" > .env
   ```

## Usage

### Basic Scan
```bash
secretscan --repo https://github.com/user/repo --n 10 --out report.json
```

### Scan Local Repository
```bash
secretscan --repo /path/to/local/repo --n 20 --branch main
```

### Scan Specific Branch
```bash
secretscan --repo https://github.com/user/repo --branch develop --n 5
```

## How It Works

1. **Git Scanning**: Clones/loads repository and extracts last N commits with diffs
2. **Heuristic Analysis**: Fast regex pattern matching for common secret formats
3. **LLM Analysis**: Gemini AI analyzes diffs for context-dependent secrets
4. **Merging**: Combines results, deduplicates, and boosts confidence for findings detected by both
5. **Reporting**: Generates detailed JSON report with confidence scores

## Output Format

```json
{
  "timestamp": "2025-11-02T10:30:00",
  "repo": "https://github.com/user/repo",
  "commits_scanned": 10,
  "total_findings": 3,
  "findings": [
    {
      "commit_hash": "abc123def456",
      "file_path": "config.py",
      "line_number": 15,
      "snippet": "API_KEY = \"sk_test_4eC39HqLy...\"",
      "finding_type": "stripe_key",
      "confidence": 0.9,
      "rationale": "Stripe API key"
    }
  ]
}
```

## Requirements

- Python 3.8+
- Git
- Google Gemini API Key

## Dependencies

```
click>=8.0
gitpython>=3.1.0
pydantic>=2.0
langchain-google-genai>=0.0.6
python-dotenv>=1.0
```

## Architecture

```
cybersec_scanner/
├── scanner.py      # Git repository scanner
├── analyzer.py     # Heuristic + LLM analyzers
└── cli_utils.py    # CLI interface
```

## Testing

Test on intentionally vulnerable repositories:

```bash
# Test repo with fake secrets
secretscan --repo https://github.com/trufflesecurity/test_keys --n 20
```

## Limitations

- Requires API key (costs may apply for large scans)
- LLM analysis may be slow for repos with many commits
- Binary files are skipped
- Shallow analysis (doesn't check entire file history)

## Acknowledgments

- Built with [LangChain](https://python.langchain.com/) and [Google Gemini](https://ai.google.dev/)
- Inspired by tools like [gitleaks](https://github.com/gitleaks/gitleaks) and [trufflehog](https://github.com/trufflesecurity/trufflehog)

## Support

Found a bug? [Open an issue](https://github.com/marinamomina/cybersec-scanner/issues)




