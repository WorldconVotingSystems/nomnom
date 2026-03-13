# Issue #200 - Utility Functions

from datetime import datetime
from typing import List, Optional
import hashlib


def format_date(date: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    return date.strftime(format_str)


def generate_hash(input_str: str) -> str:
    return hashlib.md5(input_str.encode()).hexdigest()


def truncate_string(s: str, max_length: int = 50, suffix: str = "...") -> str:
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def is_safe_string(input_str: str) -> bool:
    if not input_str:
        return False
    
    dangerous_keywords = [
        'DROP TABLE', 'DELETE FROM', 'UNION SELECT',
        'exec(', 'eval(', '__import__',
        'system(', 'os.system',
    ]
    
    input_lower = input_str.lower()
    return not any(kw in input_lower for kw in dangerous_keywords)


# Tests
assert format_date(datetime.now())[:4] == "2026"
assert generate_hash("test") == "098f6bcd4621d373cade4e832627b4f6cd"
assert is_safe_string("normal text") == True
assert is_safe_string("DROP TABLE") == False
