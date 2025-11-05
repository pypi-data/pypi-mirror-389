#!/usr/bin/env python3
"""SemBicho CLI v2.2.0 - Production Ready with Auth & Quality"""

import argparse
import sys
import os
from pathlib import Path
from dataclasses import asdict
import json

try:
    from .__version__ import __version__
except ImportError:
    __version__ = "2.2.0"

try:
    from .scanner import SemBichoScanner
    from .auth_module import SemBichoAuth
    from .linting_engine import LintingEngine
    from .complexity_engine import ComplexityEngine
    from .quality_integrator import QualityScannerIntegrator
except ImportError:
    from scanner import SemBichoScanner
    from auth_module import SemBichoAuth
    from linting_engine import LintingEngine
    from complexity_engine import ComplexityEngine
    from quality_integrator import QualityScannerIntegrator

def main():
    # Descripción mejorada con ejemplos
    description = """
SemBicho CLI - Enterprise Security Analysis Tool

QUICK START:
  sembicho scan --path ./myproject --output report.json
  sembicho quality all --path ./src
  sembicho auth login --token YOUR_JWT_TOKEN

EXAMPLES:
  # Scan for vulnerabilities
  sembicho scan --path . --output results.json
  
  # Code quality analysis
  sembicho quality lint --path src/
  sembicho quality complexity --path app/
  sembicho quality all --path .
  
  # Authentication
  sembicho auth login --token eyJhbGc...
  sembicho auth status
  sembicho auth logout
  
  # Version info
  sembicho version
  sembicho --version

DOCUMENTATION:
  https://docs.sembicho.com
  https://app.sembicho.com
"""
    
    parser = argparse.ArgumentParser(
        prog='sembicho', 
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--version', action='version', version=f'v{__version__}')
    subparsers = parser.add_subparsers(dest='command')
    
    # Scan
    scan_parser = subparsers.add_parser(
        'scan', 
        help='Scan code for security vulnerabilities',
        description='Analyze code for security issues and generate detailed vulnerability reports'
    )
    scan_parser.add_argument('--path', '-p', required=True, help='Path to directory or file to scan')
    scan_parser.add_argument('--output', '-o', help='Output JSON file path (default: sembicho-report.json)')
    
    # Auth (Enterprise feature)
    auth_parser = subparsers.add_parser(
        'auth', 
        help='Manage authentication with SemBicho backend',
        description='Authenticate using JWT tokens from https://app.sembicho.com'
    )
    auth_sub = auth_parser.add_subparsers(dest='auth_command')
    
    # Auth login (token-based)
    login_parser = auth_sub.add_parser(
        'login', 
        help='Login with JWT token',
        description='Authenticate using JWT token from dashboard or SEMBICHO_TOKEN env var'
    )
    login_parser.add_argument('--token', '-t', help='JWT token from https://app.sembicho.com/settings/tokens or env SEMBICHO_TOKEN')
    login_parser.add_argument('--api-url', help='Backend API URL (default: https://sembichobackend.onrender.com)')
    
    # Auth logout  
    auth_sub.add_parser(
        'logout', 
        help='Logout and clear stored credentials',
        description='Remove stored JWT token from secure keyring'
    )
    
    # Auth status
    auth_sub.add_parser(
        'status', 
        help='Check authentication and connectivity status',
        description='Verify backend connection and token validation'
    )
    
    # Quality commands (formerly integrated in scan)
    quality_parser = subparsers.add_parser(
        'quality', 
        help='Analyze code quality metrics',
        description='Run linting, complexity analysis, or combined quality checks'
    )
    quality_sub = quality_parser.add_subparsers(dest='quality_command')
    
    # Lint command
    lint_parser = quality_sub.add_parser(
        'lint', 
        help='Run code linting analysis',
        description='Check code style and quality issues using flake8/pylint'
    )
    lint_parser.add_argument('--path', '-p', required=True, help='Path to directory or file to analyze')
    lint_parser.add_argument('--language', '-l', choices=['python', 'javascript'], help='Target language (auto-detected if not specified)')
    lint_parser.add_argument('--output', '-o', help='Save results to JSON file')
    lint_parser.add_argument('--format', choices=['json', 'console'], default='console', help='Output format (default: console)')
    
    # Complexity command
    complexity_parser = quality_sub.add_parser(
        'complexity', 
        help='Analyze cyclomatic complexity',
        description='Measure code complexity using radon (McCabe complexity metrics)'
    )
    complexity_parser.add_argument('--path', '-p', required=True, help='Path to directory or file to analyze')
    complexity_parser.add_argument('--threshold', '-t', choices=['low', 'moderate', 'high'], default='moderate', help='Complexity threshold (default: moderate)')
    complexity_parser.add_argument('--output', '-o', help='Save results to JSON file')
    complexity_parser.add_argument('--format', choices=['json', 'console'], default='console', help='Output format (default: console)')
    
    # Quality (all-in-one)
    quality_all_parser = quality_sub.add_parser(
        'all', 
        help='Run complete quality analysis',
        description='Execute both linting and complexity analysis in one command'
    )
    quality_all_parser.add_argument('--path', '-p', required=True, help='Path to directory or file to analyze')
    quality_all_parser.add_argument('--output', '-o', help='Save combined results to JSON file')
    quality_all_parser.add_argument('--format', choices=['json', 'console'], default='console', help='Output format (default: console)')
    
    # Version
    subparsers.add_parser(
        'version', 
        help='Show CLI version',
        description='Display the current version of SemBicho CLI'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'scan':
        print(f"")
        print(f"  SemBicho CLI v{__version__:29s} ")
        print(f"")
        
        target = Path(args.path).resolve()
        if not target.exists():
            print(f"\n Error: Path not found: {target}")
            sys.exit(1)
        
        print(f"\n Scanning: {target}")
        scanner = SemBichoScanner()
        result = scanner.scan_directory(str(target))
        
        files = result.quality_metrics.total_files_scanned
        vulns = result.total_vulnerabilities
        print(f"\n Scan completed!")
        print(f"   Files scanned: {files}")
        print(f"   Vulnerabilities found: {vulns}")
        print(f"   Critical: {result.severity_counts.get('critical', 0)}")
        print(f"   High: {result.severity_counts.get('high', 0)}")
        print(f"   Medium: {result.severity_counts.get('medium', 0)}")
        print(f"   Low: {result.severity_counts.get('low', 0)}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2, ensure_ascii=False)
            print(f"\n Results saved to: {args.output}")
    
    elif args.command == 'auth':
        auth_handler = SemBichoAuth()
        
        if not args.auth_command:
            print("Auth commands: login, logout, status")
            print("Run 'sembicho auth --help' for more info")
            return
        
        if args.auth_command == 'login':
            # Get token from args or environment variable or interactive input
            token = args.token or os.environ.get('SEMBICHO_TOKEN')
            
            if not token:
                # Interactive input
                print("\n🔐 SemBicho CLI - Token Authentication")
                print("=" * 50)
                token = input("\n🔑 Enter your JWT token: ").strip()
            
            if not token:
                print("\n❌ Error: Token is required")
                print("\n📖 How to get your token:")
                print("   1. Go to https://app.sembicho.com")
                print("   2. Login with your credentials")
                print("   3. Navigate to Settings > API Tokens")
                print("   4. Click 'Generate New Token'")
                print("   5. Copy the token")
                print("\n💻 Usage:")
                print("   sembicho auth login --token YOUR_TOKEN")
                print("   # OR")
                print("   export SEMBICHO_TOKEN=YOUR_TOKEN")
                print("   sembicho auth login")
                sys.exit(1)
            
            print("\n🔄 Validating token...")
            if auth_handler.login_with_token(token, args.api_url):
                print("\n✅ Authentication successful!")
                status = auth_handler.get_auth_status()
                print(f"   👤 User: {status['username']}")
                print(f"   🌐 API: {status['api_url']}")
                print(f"   📅 Login: {status['last_login']}")
                print("\n💡 You can now use authenticated features:")
                print("   • Upload scan results: sembicho scan --path . --upload")
                print("   • View dashboard: https://app.sembicho.com/dashboard")
                print("   • Check status: sembicho auth status")
            else:
                print("\n❌ Authentication failed")
                print("   Please check your token and try again")
                sys.exit(1)
        
        elif args.auth_command == 'logout':
            if auth_handler.logout():
                print("✅ Logged out successfully")
            else:
                print("❌ Logout failed")
        
        elif args.auth_command == 'status':
            status = auth_handler.get_auth_status()
            print(f"Authentication Status:")
            print(f"  Authenticated: {'✅ Yes' if status['authenticated'] else '❌ No'}")
            print(f"  Username: {status['username']}")
            print(f"  API URL: {status['api_url']}")
            print(f"  Last Login: {status['last_login']}")
            print(f"  Config: {status['config_path']}")
            
            # Test connection based on authentication status
            if status['authenticated']:
                # User has token, test authenticated connection
                if auth_handler.test_authenticated_connection():
                    print(f"  Backend: ✅ Connected & Authenticated")
                else:
                    print(f"  Backend: ❌ Authentication Failed (invalid token)")
            else:
                # No token, test basic connectivity only
                if auth_handler.test_connection():
                    print(f"  Backend: 🟡 Reachable (not authenticated)")
                else:
                    print(f"  Backend: ❌ Unreachable")
    
    elif args.command == 'quality':
        if not args.quality_command:
            print("Quality commands: lint, complexity, all")
            print("Run 'sembicho quality --help' for more info")
            return
        
        target = Path(args.path).resolve()
        if not target.exists():
            print(f"\n Error: Path not found: {target}")
            sys.exit(1)
        
        print(f"\n SemBicho CLI v{__version__} - Quality Analysis")
        print(f" Target: {target}")
        
        if args.quality_command == 'lint':
            print(f"\n Running linting analysis...")
            engine = LintingEngine()
            
            # Determine language
            language = args.language
            if not language:
                # Auto-detect based on file extension
                if target.suffix == '.py':
                    language = 'python'
                elif target.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                    language = 'javascript'
                else:
                    print(f"Unsupported file type: {target.suffix}")
                    print("Supported: .py, .js, .jsx, .ts, .tsx")
                    sys.exit(1)
            
            # Run linting analysis
            vulnerabilities, metrics = engine.run_linting_analysis(str(target), language)
            
            # Display results
            if args.format == 'console':
                print(f"\n Linting Results:")
                print(f"   Issues Found: {len(vulnerabilities)}")
                print(f"   Total Lint Issues: {metrics.total_lint_issues}")
                print(f"   Style Issues: {metrics.style_issues}")
                print(f"   Performance Issues: {metrics.performance_issues}")
                print(f"   Linting Score: {metrics.linting_score:.1f}/100")
                
                for vuln in vulnerabilities[:10]:  # Show first 10
                    severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(vuln.severity, "⚪")
                    print(f"   {severity_icon} {vuln.severity}: {vuln.message} (Line {vuln.line})")
                if len(vulnerabilities) > 10:
                    print(f"   ... and {len(vulnerabilities) - 10} more issues")
            
            if args.output:
                result_data = {
                    "vulnerabilities": [asdict(v) for v in vulnerabilities],
                    "metrics": asdict(metrics),
                    "summary": {
                        "total_issues": len(vulnerabilities),
                        "language": language,
                        "file": str(target)
                    }
                }
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, indent=2, ensure_ascii=False)
                print(f"\n Results saved to: {args.output}")
        
        elif args.quality_command == 'complexity':
            print(f"\n Running complexity analysis...")
            engine = ComplexityEngine()
            
            # Determine language
            if target.suffix == '.py':
                language = 'python'
            elif target.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                language = 'javascript'
            else:
                print(f"Complexity analysis supports Python (.py) and JavaScript (.js, .jsx, .ts, .tsx) files")
                sys.exit(1)
            
            result = engine.analyze_complexity(str(target), language)
            
            # Display results
            if args.format == 'console':
                print(f"\n Complexity Results:")
                print(f"   Functions Analyzed: {result.total_functions}")
                print(f"   Average Complexity: {result.average_complexity:.2f}")
                print(f"   Max Complexity: {result.max_complexity}")
                print(f"   Complexity Grade: {result.complexity_grade}")
                print(f"   Complexity Score: {result.complexity_score:.1f}/100")
                print(f"   High Complexity (>10): {result.high_complexity_count}")
                print(f"   Critical Complexity (>20): {result.critical_complexity_count}")
                
                # Show complexity metrics
                if result.complexity_metrics:
                    print(f"\n   Top Complex Functions:")
                    sorted_metrics = sorted(result.complexity_metrics, key=lambda x: x.cyclomatic_complexity, reverse=True)
                    for metric in sorted_metrics[:5]:  # Top 5 most complex
                        level_icon = {"LOW": "🟢", "MODERATE": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}.get(metric.complexity_level.value.upper(), "⚪")
                        print(f"   {level_icon} {metric.name}: {metric.cyclomatic_complexity} ({metric.complexity_level.value}) - Line {metric.line_number}")
                else:
                    print(f"   No functions found for analysis")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(asdict(result), f, indent=2, ensure_ascii=False)
                print(f"\n Results saved to: {args.output}")
        
        elif args.quality_command == 'all':
            print(f"\n Running complete quality analysis...")
            integrator = QualityScannerIntegrator()
            result = integrator.analyze_quality(str(target))
            
            # Display summary
            if args.format == 'console':
                print(f"\n Quality Analysis Results:")
                print(f"   Quality Grade: {result.quality_grade}")
                print(f"   Quality Score: {result.quality_score:.1f}/100")
                print(f"   Total Issues: {result.total_quality_issues}")
                print(f"   Execution Time: {result.execution_time:.2f}s")
                
                print(f"\n Issue Breakdown:")
                print(f"   Linting Issues: {len(result.linting_issues)}")
                print(f"   Complexity Issues: {len(result.complexity_issues)}")
                print(f"   Code Smells: {len(result.code_smells)}")
                
                # Show top issues
                all_issues = result.linting_issues + result.complexity_issues + result.code_smells
                if all_issues:
                    print(f"\n Top Issues:")
                    for issue in all_issues[:5]:  # Top 5 issues
                        severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}.get(issue.severity, "⚪")
                        print(f"   {severity_icon} {issue.severity}: {issue.message} (Line {issue.line})")
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(asdict(result), f, indent=2, ensure_ascii=False)
                print(f"\n Results saved to: {args.output}")
    
    elif args.command == 'version':
        print(f"SemBicho CLI v{__version__}")

if __name__ == '__main__':
    main()
