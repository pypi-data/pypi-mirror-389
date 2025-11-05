import click
import json
from datetime import datetime
from dotenv import load_dotenv
import os

from cybersec_scanner.scanner import GitRepoScanner
from cybersec_scanner.secret_analyzer import SecretAnalyzer
from cybersec_scanner.broken_access_analyzer import BrokenAccessAnalyzer
from cybersec_scanner.injection_analyzer import InjectionAnalyzer
from cybersec_scanner.design_analyser import DesignAnalyzer
from cybersec_scanner.security_misconfig_analyzer import SecurityMisconfigAnalyzer

load_dotenv()


@click.command()
@click.option('--repo', required=True, help='Repository URL or path')
@click.option('--n', type=int, default=10, help='Number of commits to scan')
@click.option('--branch', default='HEAD', help='Branch to scan')
@click.option('--out', default='report.json', help='Output JSON file')
@click.option('--analyzers', '-a', 
              type=click.Choice(['secrets', 'access', 'injection', 'design', 'secmisconfig' , 'all'], case_sensitive=False),
              multiple=True,
              default=['all'],
              help='Analyzers to run (can specify multiple: -a secrets -a access)')
def scan(repo, n, branch, out, analyzers):
    """Scan git repository for vulnerabilities"""
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        click.echo("❌ Error: OPENAI_API_KEY not set in .env", err=True)
        return
    

    # Determine which analyzers to run
    run_secrets = 'secrets' in analyzers or 'all' in analyzers
    run_access = 'access' in analyzers or 'all' in analyzers
    run_injection = 'injection' in analyzers or 'all' in analyzers
    run_design = 'design' in analyzers or 'all' in analyzers
    run_secmisconfig = 'secmisconfig' in analyzers or 'all' in analyzers
    
    # Scan commits
    click.echo(f"📂 Scanning {repo} (last {n} commits)...")
    scanner = GitRepoScanner(repo, n, branch)
    commits = scanner.scan()
    click.echo(f"✓ Found {len(commits)} commits\n")
    
    all_findings = {}
    
    # Run Secret Analyzer
    if run_secrets:
        click.echo("🔍 Running Secret Analyzer...")
        analyzer = SecretAnalyzer(api_key, repo)
        findings = analyzer.analyze(commits)
        all_findings['secrets'] = findings
        click.echo(f"✓ Secrets: {len(findings)} findings\n")
    
    # Run Broken Access Analyzer
    if run_access:
        click.echo("🔍 Running Broken Access Analyzer...")
        analyzer = BrokenAccessAnalyzer(repo, api_key)
        findings = analyzer.analyze(commits)
        all_findings['broken_access'] = findings
        click.echo(f"✓ Access Control: {len(findings)} findings\n")

    if run_injection:
        click.echo("🔍 Running Injection Analyzer...")
        analyzer = InjectionAnalyzer(repo, api_key)
        findings = analyzer.analyze(commits)
        all_findings['injection'] = findings
        click.echo(f"✓ Injection Control: {len(findings)} findings\n")


    if run_design:
        click.echo("🔍 Running Design Analyzer...")
        analyzer = DesignAnalyzer(repo, api_key)
        findings = analyzer.analyze(commits)
        all_findings['design'] = findings
        click.echo(f"✓ Design Control: {len(findings)} findings\n")

    if run_secmisconfig:
        click.echo("🔍 Running Security Misconfiguration Analyzer...")
        analyzer = SecurityMisconfigAnalyzer(repo, api_key)
        findings = analyzer.analyze(commits)
        all_findings['security_misconfiguration'] = findings
        click.echo(f"✓ Security Misconfiguration Control: {len(findings)} findings\n")

    # Build report
    total_findings = sum(len(findings) for findings in all_findings.values())
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'repo': repo,
        'commits_scanned': len(commits),
        'analyzers_run': list(all_findings.keys()),
        'total_findings': total_findings,
        'findings': {
            analyzer: [f.model_dump() for f in findings]
            for analyzer, findings in all_findings.items()
        }
    }
    
    # Save report
    with open(out, 'w') as f:
        json.dump(report, f, indent=2)
    
    click.echo(f"✅ Done! Found {total_findings} total findings")
    click.echo(f"📄 Report saved to: {out}")


if __name__ == '__main__':
    scan()