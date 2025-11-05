#!/usr/bin/env python3
"""SemBicho CLI v2.1.4"""

import argparse
import sys
from pathlib import Path
from dataclasses import asdict
import json

try:
    from .__version__ import __version__
except ImportError:
    __version__ = "2.1.4"

try:
    from .scanner import SemBichoScanner
except ImportError:
    from scanner import SemBichoScanner

def main():
    parser = argparse.ArgumentParser(prog='sembicho', description='SemBicho CLI - Security Analysis Tool')
    parser.add_argument('--version', action='version', version=f'v{__version__}')
    subparsers = parser.add_subparsers(dest='command')
    
    # Scan
    scan_parser = subparsers.add_parser('scan', help='Scan code for vulnerabilities')
    scan_parser.add_argument('--path', '-p', required=True, help='Path to scan')
    scan_parser.add_argument('--output', '-o', help='Output file')
    
    # Auth
    auth_parser = subparsers.add_parser('auth', help='Authentication management')
    auth_sub = auth_parser.add_subparsers(dest='auth_command')
    auth_sub.add_parser('login', help='Login to backend')
    auth_sub.add_parser('logout', help='Logout')
    auth_sub.add_parser('status', help='Check auth status')
    
    # Version
    subparsers.add_parser('version', help='Show version')
    
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
        if not args.auth_command:
            print("Auth commands: login, logout, status")
            print("Run 'sembicho auth --help' for more info")
        else:
            print(f"Auth: {args.auth_command}")
            print("Full authentication will be available in next version")
    
    elif args.command == 'version':
        print(f"SemBicho CLI v{__version__}")

if __name__ == '__main__':
    main()
