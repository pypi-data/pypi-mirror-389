#!/usr/bin/env python3
"""
Test script for Alprina API.
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"


def test_root():
    """Test root endpoint."""
    print("=" * 60)
    print("Testing: GET /")
    print("=" * 60)
    response = requests.get(f"{API_BASE}/")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def test_health():
    """Test health check."""
    print("=" * 60)
    print("Testing: GET /health")
    print("=" * 60)
    response = requests.get(f"{API_BASE}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def test_list_agents():
    """Test agent listing."""
    print("=" * 60)
    print("Testing: GET /v1/agents")
    print("=" * 60)
    response = requests.get(f"{API_BASE}/v1/agents")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total agents: {data['total']}")
    print(f"Engine: {data['security_engine']}")
    print("\nAgents:")
    for agent in data['agents']:
        print(f"  - {agent['display_name']}: {agent['description'][:60]}...")
    print()


def test_scan_code():
    """Test code scanning."""
    print("=" * 60)
    print("Testing: POST /v1/scan/code")
    print("=" * 60)

    vulnerable_code = """
# Hardcoded API key - BAD!
API_KEY = "sk-1234567890abcdef"

def login(username, password):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return query

# Debug mode enabled
DEBUG = True
"""

    payload = {
        "code": vulnerable_code,
        "language": "python",
        "profile": "code-audit",
        "safe_only": True
    }

    print(f"Scanning code ({len(vulnerable_code)} chars)...")
    start = time.time()
    response = requests.post(f"{API_BASE}/v1/scan/code", json=payload)
    duration = time.time() - start

    print(f"Status: {response.status_code}")
    print(f"Request took: {duration:.2f}s")

    if response.status_code == 200:
        data = response.json()
        print(f"\nScan ID: {data['scan_id']}")
        print(f"Status: {data['status']}")
        print(f"Engine: {data['alprina_engine']}")
        print(f"Duration: {data.get('duration_ms', 'N/A')}ms")
        print(f"\nFindings: {data['summary']['total_findings']}")
        print(f"  HIGH: {data['summary']['high']}")
        print(f"  MEDIUM: {data['summary']['medium']}")
        print(f"  LOW: {data['summary']['low']}")

        if data['findings']:
            print("\nDetailed Findings:")
            for finding in data['findings'][:3]:  # Show first 3
                print(f"\n  [{finding['severity']}] {finding['type']}")
                print(f"  {finding['description']}")
                if finding.get('location'):
                    print(f"  Location: {finding['location']}")
    else:
        print(f"Error: {response.text}")
    print()


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("ALPRINA API TEST SUITE")
    print("=" * 60)
    print()

    # Wait for server to be ready
    print("Waiting for API server...")
    for i in range(10):
        try:
            requests.get(f"{API_BASE}/health", timeout=1)
            print("✓ Server is ready!\n")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    else:
        print("✗ Server not responding")
        return

    # Run tests
    try:
        test_root()
        test_health()
        test_list_agents()
        test_scan_code()

        print("=" * 60)
        print("✅ ALL API TESTS PASSED!")
        print("=" * 60)
        print()
        print("API Documentation: http://localhost:8000/docs")
        print("Alternative Docs: http://localhost:8000/redoc")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
