#!/usr/bin/env python3
"""
Suture System Health Checker
Proactive system health monitoring
"""

import os
import subprocess
import shutil
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str  # 'ok', 'warning', 'critical'
    message: str
    details: Dict = None
    suggestions: List[str] = None


class SystemHealthChecker:
    """Perform system health checks"""
    
    def __init__(self):
        self.checks = []
    
    def run_command(self, command: List[str]) -> Tuple[bool, str, str]:
        """Run system command and return output"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def check_disk_space(self) -> HealthCheck:
        """Check available disk space"""
        try:
            stat = shutil.disk_usage('/')
            percent_used = (stat.used / stat.total) * 100
            free_gb = stat.free / (1024**3)
            
            if percent_used >= 95:
                return HealthCheck(
                    name="Disk Space",
                    status="critical",
                    message=f"Critical: Only {free_gb:.1f}GB free ({100-percent_used:.1f}% available)",
                    details={'used_percent': percent_used, 'free_gb': free_gb},
                    suggestions=[
                        "Clean package cache: sudo dnf clean all",
                        "Remove old logs: sudo journalctl --vacuum-time=7d",
                        "Find large files: du -sh /* | sort -h"
                    ]
                )
            elif percent_used >= 85:
                return HealthCheck(
                    name="Disk Space",
                    status="warning",
                    message=f"Warning: {free_gb:.1f}GB free ({100-percent_used:.1f}% available)",
                    details={'used_percent': percent_used, 'free_gb': free_gb},
                    suggestions=["Consider cleaning up old files"]
                )
            else:
                return HealthCheck(
                    name="Disk Space",
                    status="ok",
                    message=f"{free_gb:.1f}GB free ({100-percent_used:.1f}% available)",
                    details={'used_percent': percent_used, 'free_gb': free_gb}
                )
        except Exception as e:
            return HealthCheck(
                name="Disk Space",
                status="warning",
                message=f"Unable to check: {e}"
            )
    
    def check_memory(self) -> HealthCheck:
        """Check available memory"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem_info = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    mem_info[key.strip()] = int(value.strip().split()[0])
            
            total = mem_info.get('MemTotal', 0) / 1024  # MB
            available = mem_info.get('MemAvailable', 0) / 1024  # MB
            percent_used = ((total - available) / total) * 100 if total > 0 else 0
            
            if percent_used >= 90:
                return HealthCheck(
                    name="Memory",
                    status="critical",
                    message=f"Critical: {percent_used:.1f}% used, {available:.0f}MB available",
                    details={'percent_used': percent_used, 'available_mb': available},
                    suggestions=[
                        "Identify memory hogs: ps aux --sort=-%mem | head",
                        "Check for memory leaks",
                        "Restart high-memory services"
                    ]
                )
            elif percent_used >= 80:
                return HealthCheck(
                    name="Memory",
                    status="warning",
                    message=f"Warning: {percent_used:.1f}% used, {available:.0f}MB available",
                    details={'percent_used': percent_used, 'available_mb': available}
                )
            else:
                return HealthCheck(
                    name="Memory",
                    status="ok",
                    message=f"{percent_used:.1f}% used, {available:.0f}MB available",
                    details={'percent_used': percent_used, 'available_mb': available}
                )
        except Exception as e:
            return HealthCheck(
                name="Memory",
                status="warning",
                message=f"Unable to check: {e}"
            )
    
    def check_failed_services(self) -> HealthCheck:
        """Check for failed systemd services"""
        success, stdout, stderr = self.run_command(['systemctl', '--failed', '--no-pager', '--no-legend'])
        
        if not success:
            return HealthCheck(
                name="Failed Services",
                status="warning",
                message="Unable to check systemd services"
            )
        
        # Parse failed services - skip the bullet point and get service name
        failed_services = []
        for line in stdout.strip().split('\n'):
            if line.strip():
                parts = line.split()
                # Skip the bullet point (●) and get the actual service name (second column)
                if len(parts) >= 2 and parts[0] == '●':
                    service_name = parts[1]
                    failed_services.append(service_name)
                elif len(parts) >= 1 and parts[0] != '●':
                    failed_services.append(parts[0])
        
        if failed_services:
            return HealthCheck(
                name="Failed Services",
                status="critical",
                message=f"Found {len(failed_services)} failed service(s)",
                details={'services': failed_services},
                suggestions=[
                    f"Check status: systemctl status {failed_services[0]}",
                    f"View logs: journalctl -u {failed_services[0]} -n 50",
                    "Restart service: sudo systemctl restart <service>"
                ]
            )
        else:
            return HealthCheck(
                name="Failed Services",
                status="ok",
                message="All services running normally"
            )
    
    def check_system_updates(self) -> HealthCheck:
        """Check for available system updates"""
        success, stdout, stderr = self.run_command(['dnf', 'check-update', '-q'])
        
        # dnf check-update returns 100 if updates are available
        if not success and "exit status 100" not in stderr:
            update_count = len([line for line in stdout.strip().split('\n') if line and not line.startswith('Last')])
            
            if update_count > 50:
                return HealthCheck(
                    name="System Updates",
                    status="warning",
                    message=f"{update_count} updates available",
                    suggestions=["Update system: sudo dnf update -y"]
                )
            elif update_count > 0:
                return HealthCheck(
                    name="System Updates",
                    status="ok",
                    message=f"{update_count} updates available",
                    suggestions=["Update system: sudo dnf update"]
                )
        
        return HealthCheck(
            name="System Updates",
            status="ok",
            message="System is up to date"
        )
    
    def check_log_errors(self, analyzer) -> HealthCheck:
        """Check recent system logs for errors"""
        success, stdout, stderr = self.run_command([
            'journalctl', '-p', 'err', '-n', '50', '--no-pager'
        ])
        
        if not success:
            return HealthCheck(
                name="Recent Errors",
                status="warning",
                message="Unable to check system logs (may need sudo)"
            )
        
        if stdout.strip():
            matches = analyzer.analyze_text(stdout)
            
            if len(matches) > 10:
                return HealthCheck(
                    name="Recent Errors",
                    status="warning",
                    message=f"Found {len(matches)} errors in recent logs",
                    suggestions=["Run: suture analyze /var/log/messages"]
                )
            elif matches:
                return HealthCheck(
                    name="Recent Errors",
                    status="ok",
                    message=f"Found {len(matches)} minor errors",
                    suggestions=["Review with: journalctl -p err"]
                )
        
        return HealthCheck(
            name="Recent Errors",
            status="ok",
            message="No significant errors in recent logs"
        )
    
    def check_selinux_denials(self) -> HealthCheck:
        """Check for SELinux denials"""
        audit_log = '/var/log/audit/audit.log'
        
        # Check if audit log exists and is accessible
        try:
            # Try to check if we can access it
            success, stdout, stderr = self.run_command([
                'sudo', '-n', 'grep', '-c', 'denied', audit_log
            ])
            
            if success and stdout.strip():
                denial_count = int(stdout.strip())
                
                if denial_count > 10:
                    return HealthCheck(
                        name="SELinux",
                        status="warning",
                        message=f"Found {denial_count} SELinux denials",
                        suggestions=[
                            "View denials: sudo ausearch -m avc -ts recent",
                            "Generate policy: sudo audit2allow -a",
                            "Check mode: getenforce"
                        ]
                    )
            
            return HealthCheck(
                name="SELinux",
                status="ok",
                message="No recent SELinux denials"
            )
            
        except (PermissionError, FileNotFoundError):
            # Try without sudo
            try:
                if os.path.exists(audit_log):
                    return HealthCheck(
                        name="SELinux",
                        status="ok",
                        message="SELinux check requires sudo privileges"
                    )
            except PermissionError:
                pass
            
            # SELinux might be disabled or we don't have permissions
            return HealthCheck(
                name="SELinux",
                status="ok",
                message="SELinux audit log not accessible (may be disabled or need sudo)"
            )
    
    def run_all_checks(self, analyzer=None) -> List[HealthCheck]:
        """Run all health checks"""
        checks = [
            self.check_disk_space(),
            self.check_memory(),
            self.check_failed_services(),
            self.check_system_updates(),
            self.check_selinux_denials(),
        ]
        
        if analyzer:
            checks.append(self.check_log_errors(analyzer))
        
        return checks
    
    def get_overall_status(self, checks: List[HealthCheck]) -> str:
        """Determine overall system health status"""
        if any(c.status == 'critical' for c in checks):
            return 'critical'
        elif any(c.status == 'warning' for c in checks):
            return 'warning'
        else:
            return 'healthy'
