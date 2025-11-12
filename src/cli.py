#!/usr/bin/env python3
"""
Suture CLI - Command Line Interface
"""

import sys
import time
import click
from colorama import Fore, Style, init
from tabulate import tabulate
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzer import ErrorAnalyzer, ErrorMatch

# Initialize colorama
init(autoreset=True)


class Colors:
    """Color scheme for output"""
    CRITICAL = Fore.RED + Style.BRIGHT
    HIGH = Fore.RED
    MEDIUM = Fore.YELLOW
    LOW = Fore.GREEN
    INFO = Fore.CYAN
    CYAN = Fore.CYAN
    SUCCESS = Fore.GREEN + Style.BRIGHT
    RESET = Style.RESET_ALL

def print_banner():
    """Print Suture banner"""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════╗
║         🩹 SUTURE v0.1.0             ║
║   Linux Error Detection & Healing    ║
╚═══════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


def get_severity_color(severity: str) -> str:
    """Get color based on severity"""
    severity_map = {
        'critical': Colors.CRITICAL,
        'high': Colors.HIGH,
        'medium': Colors.MEDIUM,
        'low': Colors.LOW
    }
    return severity_map.get(severity.lower(), Colors.INFO)


def print_error_match(match: ErrorMatch, index: int):
    """Print a single error match with formatting"""
    color = get_severity_color(match.severity)
    
    print(f"\n{color}{'═' * 70}{Colors.RESET}")
    print(f"{color}[{index}] {match.name} ({match.rule_id}){Colors.RESET}")
    print(f"{color}{'═' * 70}{Colors.RESET}")
    
    print(f"{Colors.INFO}Severity:{Colors.RESET} {color}{match.severity.upper()}{Colors.RESET}")
    print(f"{Colors.INFO}Category:{Colors.RESET} {match.category}")
    print(f"{Colors.INFO}Line:{Colors.RESET} {match.line_number}")
    
    print(f"\n{Colors.INFO}Matched Text:{Colors.RESET}")
    print(f"  {Fore.WHITE}{match.matched_text}{Colors.RESET}")
    
    print(f"\n{Colors.INFO}Explanation:{Colors.RESET}")
    print(f"  {match.explanation}")
    
    print(f"\n{Colors.INFO}Suggested Solutions:{Colors.RESET}")
    for i, solution in enumerate(match.solutions, 1):
        print(f"  {Fore.GREEN}{i}.{Colors.RESET} {solution}")


def print_statistics(stats: dict):
    """Print analysis statistics"""
    print(f"\n{Fore.CYAN}{'═' * 70}")
    print(f"📊 ANALYSIS STATISTICS")
    print(f"{'═' * 70}{Colors.RESET}\n")
    
    print(f"Total Errors Found: {Colors.HIGH}{stats['total']}{Colors.RESET}\n")
    
    if stats['by_severity']:
        print(f"{Colors.INFO}By Severity:{Colors.RESET}")
        for severity, count in sorted(stats['by_severity'].items()):
            color = get_severity_color(severity)
            print(f"  {color}● {severity.capitalize()}: {count}{Colors.RESET}")
    
    if stats['by_category']:
        print(f"\n{Colors.INFO}By Category:{Colors.RESET}")
        for category, count in sorted(stats['by_category'].items()):
            print(f"  • {category}: {count}")


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    🩹 Suture - Linux Error Detection & Auto-Fix Tool
    
    Analyzes console output and log files to detect common errors
    and suggest solutions.
    """
    pass


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
@click.option('--stats', '-s', is_flag=True, help='Show statistics')
def analyze(file, verbose, stats):
    """Analyze a log file for errors"""
    print_banner()
    
    try:
        analyzer = ErrorAnalyzer()
        
        print(f"{Colors.INFO}Analyzing: {file}{Colors.RESET}")
        matches = analyzer.analyze_file(file)
        
        if not matches:
            print(f"\n{Colors.SUCCESS}✓ No errors detected!{Colors.RESET}")
            return
        
        print(f"\n{Colors.HIGH}Found {len(matches)} error(s):{Colors.RESET}")
        
        for i, match in enumerate(matches, 1):
            print_error_match(match, i)
        
        if stats:
            statistics = analyzer.get_statistics(matches)
            print_statistics(statistics)
            
    except Exception as e:
        print(f"{Colors.CRITICAL}Error: {e}{Colors.RESET}")
        sys.exit(1)


@cli.command()
@click.option('--input', '-i', help='Read from stdin', is_flag=True)
def scan(input):
    """Scan console output in real-time"""
    print_banner()
    
    try:
        analyzer = ErrorAnalyzer()
        
        if input:
            print(f"{Colors.INFO}Reading from stdin (Ctrl+D to finish)...{Colors.RESET}\n")
            text = sys.stdin.read()
        else:
            print(f"{Colors.INFO}Paste your console output (Ctrl+D to finish):{Colors.RESET}\n")
            text = sys.stdin.read()
        
        matches = analyzer.analyze_text(text)
        
        if not matches:
            print(f"\n{Colors.SUCCESS}✓ No errors detected!{Colors.RESET}")
            return
        
        print(f"\n{Colors.HIGH}Found {len(matches)} error(s):{Colors.RESET}")
        
        for i, match in enumerate(matches, 1):
            print_error_match(match, i)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.INFO}Scan cancelled.{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.CRITICAL}Error: {e}{Colors.RESET}")
        sys.exit(1)


@cli.command()
def rules():
    """List all available error detection rules"""
    print_banner()
    
    try:
        analyzer = ErrorAnalyzer()
        
        table_data = []
        for rule in analyzer.rules:
            color = get_severity_color(rule['severity'])
            table_data.append([
                rule['id'],
                rule['name'],
                f"{color}{rule['severity']}{Colors.RESET}",
                rule['category']
            ])
        
        print(tabulate(
            table_data,
            headers=['ID', 'Name', 'Severity', 'Category'],
            tablefmt='grid'
        ))
        
        print(f"\n{Colors.INFO}Total Rules: {len(analyzer.rules)}{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.CRITICAL}Error: {e}{Colors.RESET}")
        sys.exit(1)


@cli.command()
def categories():
    """List all error categories"""
    print_banner()
    
    try:
        analyzer = ErrorAnalyzer()
        cats = analyzer.list_categories()
        
        print(f"{Colors.INFO}Available Categories:{Colors.RESET}\n")
        for cat in cats:
            print(f"  • {cat}")
        
        print(f"\n{Colors.INFO}Total Categories: {len(cats)}{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.CRITICAL}Error: {e}{Colors.RESET}")
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--auto', '-a', is_flag=True, help='Auto-apply safe fixes')
@click.option('--dry-run', '-d', is_flag=True, help='Show commands without executing')
def fix(file, auto, dry_run):
    """Interactively fix detected errors"""
    print_banner()
    
    try:
        from fixer import InteractiveFixer
        
        analyzer = ErrorAnalyzer()
        fixer = InteractiveFixer()
        fixer.dry_run = dry_run
        
        print(f"{Colors.INFO}Analyzing: {file}{Colors.RESET}")
        matches = analyzer.analyze_file(file)
        
        if not matches:
            print(f"\n{Colors.SUCCESS}✓ No errors detected!{Colors.RESET}")
            return
        
        print(f"\n{Colors.HIGH}Found {len(matches)} error(s){Colors.RESET}")
        
        for i, match in enumerate(matches, 1):
            print(f"\n{Colors.CRITICAL}{'─' * 70}{Colors.RESET}")
            print(f"{Colors.HIGH}[{i}] {match.name}{Colors.RESET}")
            print(f"{Colors.INFO}Line {match.line_number}:{Colors.RESET} {match.matched_text}")
            
            print(f"\n{Colors.INFO}Available fixes:{Colors.RESET}")
            for j, solution in enumerate(match.solutions, 1):
                print(f"  {j}. {solution}")
            
            if auto:
                continue
            
            choice = input(f"\n{Colors.INFO}Select fix (1-{len(match.solutions)}, 's' to skip, 'q' to quit): {Colors.RESET}")
            
            if choice.lower() == 'q':
                print(f"{Colors.INFO}Exiting...{Colors.RESET}")
                break
            elif choice.lower() == 's':
                continue
            elif choice.isdigit() and 1 <= int(choice) <= len(match.solutions):
                solution = match.solutions[int(choice) - 1]
                fix_cmd = fixer.parse_solution(solution)
                
                if fix_cmd and fix_cmd.requires_input:
                    command = fixer.substitute_placeholders(fix_cmd.command)
                elif fix_cmd:
                    command = fix_cmd.command
                else:
                    print(f"{Colors.MEDIUM}⚠ Manual fix required: {solution}{Colors.RESET}")
                    continue
                
                # Check prerequisites
                prereq_ok, issues = fixer.check_prerequisites(command)
                if not prereq_ok:
                    print(f"{Colors.HIGH}Prerequisites missing:{Colors.RESET}")
                    for issue in issues:
                        print(f"  • {issue}")
                    
                    alt = fixer.suggest_alternative(command)
                    if alt:
                        print(f"{Colors.INFO}Suggested alternative: {alt}{Colors.RESET}")
                        use_alt = input("Use alternative? (y/n): ")
                        if use_alt.lower() == 'y':
                            command = alt
                    continue
                
                print(f"\n{Colors.INFO}Executing:{Colors.RESET} {command}")
                
                if not dry_run:
                    confirm = input(f"{Colors.MEDIUM}Proceed? (y/n): {Colors.RESET}")
                    if confirm.lower() != 'y':
                        continue
                
                success, stdout, stderr = fixer.execute_command(command)
                
                if success:
                    print(f"{Colors.SUCCESS}✓ Fix applied successfully{Colors.RESET}")
                    if stdout:
                        print(f"Output: {stdout}")
                else:
                    print(f"{Colors.CRITICAL}✗ Fix failed{Colors.RESET}")
                    if stderr:
                        print(f"Error: {stderr}")
            
    except KeyboardInterrupt:
        print(f"\n{Colors.INFO}Interrupted by user{Colors.RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{Colors.CRITICAL}Error: {e}{Colors.RESET}")
        sys.exit(1)


@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--interval', '-i', default=1, help='Check interval in seconds')
@click.option('--journal', '-j', is_flag=True, help='Monitor systemd journal')
@click.option('--unit', '-u', help='Systemd unit to monitor')
@click.option('--alert', '-a', is_flag=True, help='Show alert for each error')
def monitor(files, interval, journal, unit, alert):
    """Monitor log files in real-time for errors"""
    print_banner()
    
    try:
        from monitor import LogMonitor, MonitorStats
        
        analyzer = ErrorAnalyzer()
        stats = MonitorStats()
        
        def on_error_detected(matches, source):
            """Callback when error is detected"""
            for match in matches:
                stats.add_error(match)
                
                color = get_severity_color(match.severity)
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"\n{color}[{timestamp}] {match.severity.upper()} detected in {source}{Colors.RESET}")
                print(f"{color}└─ {match.name}: {match.matched_text[:80]}{Colors.RESET}")
                
                if alert:
                    print(f"\n{Colors.INFO}Suggested fix:{Colors.RESET}")
                    print(f"  {match.solutions[0] if match.solutions else 'No automated fix available'}")
        
        monitor = LogMonitor(callback=on_error_detected)
        
        if journal:
            monitor.monitor_systemd_journal(analyzer, unit, interval)
        elif files:
            if len(files) == 1:
                monitor.monitor_file(files[0], analyzer, interval)
            else:
                monitor.monitor_multiple(list(files), analyzer, interval)
        else:
            print(f"{Colors.CRITICAL}Error: No files specified and --journal not set{Colors.RESET}")
            print(f"{Colors.INFO}Usage: suture monitor <file> or suture monitor --journal{Colors.RESET}")
            return
        
        # Print stats on exit
        print(stats.get_summary())
        
    except KeyboardInterrupt:
        print(f"\n{Colors.INFO}Monitoring stopped{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.CRITICAL}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed information')
def health(detailed):
    """Check system health and detect potential issues"""
    print_banner()
    
    try:
        from health import SystemHealthChecker
        
        print(f"{Colors.INFO}Running system health checks...{Colors.RESET}\n")
        
        checker = SystemHealthChecker()
        analyzer = ErrorAnalyzer()
        
        checks = checker.run_all_checks(analyzer)
        overall = checker.get_overall_status(checks)
        
        # Print results
        for check in checks:
            if check.status == 'ok':
                icon = f"{Colors.SUCCESS}✓{Colors.RESET}"
            elif check.status == 'warning':
                icon = f"{Colors.MEDIUM}⚠{Colors.RESET}"
            else:
                icon = f"{Colors.CRITICAL}✗{Colors.RESET}"
            
            print(f"{icon} {check.name}: {check.message}")
            
            if detailed and check.details:
                print(f"   Details: {check.details}")
            
            if check.suggestions:
                print(f"   {Colors.INFO}Suggestions:{Colors.RESET}")
                for suggestion in check.suggestions[:2]:  # Limit to 2 suggestions
                    print(f"   • {suggestion}")
            print()
        
        # Overall status
        print(f"{Colors.CYAN}{'═' * 70}{Colors.RESET}")
        if overall == 'healthy':
            print(f"{Colors.SUCCESS}Overall Status: HEALTHY ✓{Colors.RESET}")
        elif overall == 'warning':
            print(f"{Colors.MEDIUM}Overall Status: NEEDS ATTENTION ⚠{Colors.RESET}")
        else:
            print(f"{Colors.CRITICAL}Overall Status: CRITICAL ✗{Colors.RESET}")
        print(f"{Colors.CYAN}{'═' * 70}{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.CRITICAL}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    cli()
