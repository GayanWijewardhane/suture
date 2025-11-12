#!/usr/bin/env python3
"""
Suture Interactive Fixer
Provides interactive solution suggestions with command execution
"""

import os
import subprocess
import shutil
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class FixCommand:
    """Represents a fixable command"""
    description: str
    command: str
    requires_sudo: bool = False
    requires_input: bool = False
    input_placeholder: Optional[str] = None


class InteractiveFixer:
    """Interactive fix suggestion and execution system"""
    
    def __init__(self):
        self.dry_run = False
    
    def parse_solution(self, solution: str) -> Optional[FixCommand]:
        """Parse a solution string into a FixCommand"""
        # Extract command from solution text
        # Format: "Description: command"
        parts = solution.split(':', 1)
        
        if len(parts) < 2:
            return None
        
        description = parts[0].strip()
        command = parts[1].strip()
        
        # Detect if sudo is needed
        requires_sudo = command.startswith('sudo ')
        
        # Detect if input is needed (contains placeholders)
        requires_input = '<' in command and '>' in command
        
        # Extract placeholder if exists
        placeholder = None
        if requires_input:
            import re
            match = re.search(r'<([^>]+)>', command)
            if match:
                placeholder = match.group(1)
        
        return FixCommand(
            description=description,
            command=command,
            requires_sudo=requires_sudo,
            requires_input=requires_input,
            input_placeholder=placeholder
        )
    
    def substitute_placeholders(self, command: str) -> str:
        """Replace placeholders in command with user input"""
        import re
        
        placeholders = re.findall(r'<([^>]+)>', command)
        
        for placeholder in placeholders:
            user_input = input(f"Enter value for '{placeholder}': ").strip()
            if not user_input:
                user_input = placeholder  # Use placeholder as default
            
            command = command.replace(f'<{placeholder}>', user_input)
        
        return command
    
    def check_command_safety(self, command: str) -> tuple[bool, str]:
        """Check if command is safe to execute"""
        dangerous_patterns = [
            'rm -rf /',
            'dd if=',
            'mkfs.',
            ':(){:|:&};:',  # Fork bomb
            'chmod -R 777 /',
            '> /dev/sd'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command:
                return False, f"Dangerous pattern detected: {pattern}"
        
        return True, "Command appears safe"
    
    def execute_command(self, command: str, interactive: bool = True) -> tuple[bool, str, str]:
        """
        Execute a command and return success status and output
        
        Returns:
            (success, stdout, stderr)
        """
        if self.dry_run:
            return True, "[DRY RUN] Command not executed", ""
        
        # Check safety
        is_safe, safety_msg = self.check_command_safety(command)
        if not is_safe:
            return False, "", f"Safety check failed: {safety_msg}"
        
        try:
            # Use shell=True for complex commands, but be careful
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 30 seconds"
        except Exception as e:
            return False, "", f"Execution error: {str(e)}"
    
    def check_prerequisites(self, command: str) -> tuple[bool, List[str]]:
        """Check if prerequisites for command are met"""
        issues = []
        
        # Extract command name (first word after sudo if present)
        cmd_parts = command.split()
        cmd_name = cmd_parts[1] if cmd_parts[0] == 'sudo' else cmd_parts[0]
        
        # Check if command exists
        if not shutil.which(cmd_name):
            issues.append(f"Command '{cmd_name}' not found in PATH")
        
        # Check sudo availability if needed
        if 'sudo' in command and not shutil.which('sudo'):
            issues.append("sudo is not available")
        
        return len(issues) == 0, issues
    
    def suggest_alternative(self, command: str) -> Optional[str]:
        """Suggest alternative command if original is not available"""
        alternatives = {
            'dnf': ['yum', 'apt', 'zypper'],
            'apt': ['apt-get', 'dnf', 'yum'],
            'yum': ['dnf', 'apt'],
            'systemctl': ['service', 'rc-service'],
        }
        
        cmd_parts = command.split()
        cmd_name = cmd_parts[1] if cmd_parts[0] == 'sudo' else cmd_parts[0]
        
        if cmd_name in alternatives:
            for alt in alternatives[cmd_name]:
                if shutil.which(alt):
                    new_command = command.replace(cmd_name, alt, 1)
                    return new_command
        
        return None
    
    def create_backup(self, file_path: str) -> bool:
        """Create backup of file before modification"""
        try:
            backup_path = f"{file_path}.suture.backup"
            shutil.copy2(file_path, backup_path)
            return True
        except Exception:
            return False
    
    def get_command_explanation(self, command: str) -> str:
        """Provide explanation of what command does"""
        explanations = {
            'chmod': 'Changes file permissions',
            'chown': 'Changes file ownership',
            'dnf install': 'Installs a package',
            'dnf search': 'Searches for a package',
            'systemctl': 'Manages system services',
            'journalctl': 'Views system logs',
            'df': 'Shows disk space usage',
            'du': 'Shows directory space usage',
        }
        
        for key, explanation in explanations.items():
            if key in command:
                return explanation
        
        return "Executes system command"
