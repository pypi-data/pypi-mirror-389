#!/usr/bin/env python3
"""
Test file with intentional security vulnerabilities for scanning.
"""

import os

# VULN 1: Hardcoded API key
API_KEY = "sk-1234567890abcdef"

# VULN 2: Hardcoded password
DATABASE_PASSWORD = "admin123"

# VULN 3: Debug mode enabled
DEBUG = True

def login(username, password):
    """VULN 4: SQL Injection vulnerability"""
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    # execute(query)  # Vulnerable to SQL injection
    return query

def process_input(user_data):
    """VULN 5: Use of eval()"""
    result = eval(user_data)  # Dangerous!
    return result

def get_secret():
    """VULN 6: Accessing secrets insecurely"""
    secret_token = "ghp_1234567890abcdefghijklmnop"
    return secret_token

if __name__ == "__main__":
    # VULN 7: Insecure random
    import random
    session_id = random.randint(1000, 9999)
    print(f"Session ID: {session_id}")
