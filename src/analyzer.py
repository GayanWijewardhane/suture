#!/usr/bin/env python3
"""
Suture Error Analyzer
Detects and analyzes error patterns in Linux system output
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class ErrorMatch:
    """Represents a matched error pattern"""
    rule_id: str
    name: str
    severity: str
    category: str
    explanation: str
    solutions: List[str]
    matched_text: str
    line_number: int


class ErrorAnalyzer:
    """Analyzes text for known error patterns"""
    
    def __init__(self, rules_path: str = "rules/error_patterns.yaml"):
        self.rules = self._load_rules(rules_path)
        self.compiled_patterns = self._compile_patterns()
    
    def _load_rules(self, rules_path: str) -> Dict:
        """Load error rules from YAML file"""
        path = Path(rules_path)
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_path}")
        
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        
        return data.get('rules', [])
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for performance"""
        patterns = {}
        for rule in self.rules:
            try:
                patterns[rule['id']] = re.compile(rule['pattern'], re.IGNORECASE | re.MULTILINE)
            except re.error as e:
                print(f"Warning: Invalid pattern for {rule['id']}: {e}")
        
        return patterns
    
    def analyze_text(self, text: str) -> List[ErrorMatch]:
        """Analyze text and return list of matched errors"""
        matches = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for rule in self.rules:
                pattern = self.compiled_patterns.get(rule['id'])
                if not pattern:
                    continue
                
                if pattern.search(line):
                    match = ErrorMatch(
                        rule_id=rule['id'],
                        name=rule['name'],
                        severity=rule['severity'],
                        category=rule['category'],
                        explanation=rule['explanation'],
                        solutions=rule['solutions'],
                        matched_text=line.strip(),
                        line_number=line_num
                    )
                    matches.append(match)
        
        return matches
    
    def analyze_file(self, file_path: str) -> List[ErrorMatch]:
        """Analyze a log file for errors"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'r', errors='ignore') as f:
            content = f.read()
        
        return self.analyze_text(content)
    
    def get_rule_by_id(self, rule_id: str) -> Optional[Dict]:
        """Get rule details by ID"""
        for rule in self.rules:
            if rule['id'] == rule_id:
                return rule
        return None
    
    def list_categories(self) -> List[str]:
        """List all error categories"""
        categories = set(rule['category'] for rule in self.rules)
        return sorted(categories)
    
    def get_statistics(self, matches: List[ErrorMatch]) -> Dict:
        """Generate statistics from error matches"""
        if not matches:
            return {
                'total': 0,
                'by_severity': {},
                'by_category': {}
            }
        
        stats = {
            'total': len(matches),
            'by_severity': {},
            'by_category': {}
        }
        
        for match in matches:
            # Count by severity
            stats['by_severity'][match.severity] = \
                stats['by_severity'].get(match.severity, 0) + 1
            
            # Count by category
            stats['by_category'][match.category] = \
                stats['by_category'].get(match.category, 0) + 1
        
        return stats
