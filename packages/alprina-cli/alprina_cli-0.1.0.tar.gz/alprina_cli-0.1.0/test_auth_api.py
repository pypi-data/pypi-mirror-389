#!/usr/bin/env python3
"""
Test script for Alprina Authentication API.
Tests all auth endpoints (will fail gracefully until service_role key is added).
"""

import requests
import json
import sys

API_BASE = "http://localhost:8000"

def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def test_auth_endpoints_exist():
    """Test that all auth endpoints are registered."""
    print_section("Testing: Auth Endpoints Exist")

    response = requests.get(f"{API_BASE}/")
    data = response.json()

    print(f"Status: {response.status_code}")
    print(f"\nEndpoints available:")
    for name, endpoint in data["endpoints"].items():
        print(f"  ✓ {name}: {endpoint}")

    # Check if auth endpoints are listed
    has_register = "register" in data["endpoints"]
    has_login = "login" in data["endpoints"]

    if has_register and has_login:
        print(f"\n✅ Auth endpoints registered!")
    else:
        print(f"\n❌ Auth endpoints missing!")
        return False

    return True


def test_openapi_docs():
    """Test OpenAPI documentation includes auth endpoints."""
    print_section("Testing: OpenAPI Documentation")

    response = requests.get(f"{API_BASE}/openapi.json")

    if response.status_code != 200:
        print(f"❌ Failed to fetch OpenAPI spec: {response.status_code}")
        return False

    data = response.json()
    paths = data.get("paths", {})

    auth_endpoints = [
        "/v1/auth/register",
        "/v1/auth/login",
        "/v1/auth/me",
        "/v1/auth/api-keys"
    ]

    print("Checking for auth endpoints in OpenAPI spec:")
    all_found = True
    for endpoint in auth_endpoints:
        if endpoint in paths:
            print(f"  ✓ {endpoint}")
        else:
            print(f"  ✗ {endpoint} (missing)")
            all_found = False

    if all_found:
        print(f"\n✅ All auth endpoints documented!")
    else:
        print(f"\n❌ Some auth endpoints missing from docs!")

    return all_found


def test_register_endpoint():
    """Test register endpoint (will fail without service_role key)."""
    print_section("Testing: POST /v1/auth/register")

    payload = {
        "email": "test@alprina.ai",
        "password": "TestPass123!",
        "full_name": "Test User"
    }

    print(f"Attempting to register user: {payload['email']}")
    response = requests.post(
        f"{API_BASE}/v1/auth/register",
        json=payload
    )

    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")

    if response.status_code == 503:
        print("\n⏳ Expected: Database not configured (waiting for service_role key)")
        return True
    elif response.status_code == 201:
        print("\n✅ Registration successful!")
        return True
    else:
        print(f"\n❌ Unexpected response: {response.status_code}")
        return False


def test_login_endpoint():
    """Test login endpoint (will fail without service_role key)."""
    print_section("Testing: POST /v1/auth/login")

    payload = {
        "email": "test@alprina.ai",
        "password": "TestPass123!"
    }

    print(f"Attempting to login: {payload['email']}")
    response = requests.post(
        f"{API_BASE}/v1/auth/login",
        json=payload
    )

    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")

    if response.status_code == 503:
        print("\n⏳ Expected: Database not configured (waiting for service_role key)")
        return True
    elif response.status_code == 200:
        print("\n✅ Login successful!")
        return True
    else:
        print(f"\n❌ Unexpected response: {response.status_code}")
        return False


def test_me_endpoint_without_auth():
    """Test /me endpoint without authentication."""
    print_section("Testing: GET /v1/auth/me (No Auth)")

    print("Attempting to access without API key...")
    response = requests.get(f"{API_BASE}/v1/auth/me")

    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")

    if response.status_code == 401:
        print("\n✅ Correctly rejected unauthorized request!")
        return True
    else:
        print(f"\n❌ Should return 401, got {response.status_code}")
        return False


def test_api_keys_endpoint_without_auth():
    """Test /api-keys endpoint without authentication."""
    print_section("Testing: GET /v1/auth/api-keys (No Auth)")

    print("Attempting to access without API key...")
    response = requests.get(f"{API_BASE}/v1/auth/api-keys")

    print(f"Status: {response.status_code}")

    try:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    except:
        print(f"Response: {response.text}")

    if response.status_code == 401:
        print("\n✅ Correctly rejected unauthorized request!")
        return True
    else:
        print(f"\n❌ Should return 401, got {response.status_code}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("ALPRINA AUTHENTICATION API TEST SUITE")
    print("=" * 70)
    print()

    # Wait for server
    print("Checking if API server is running...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code == 200:
            print("✓ Server is ready!\n")
        else:
            print(f"✗ Server returned {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("✗ Server not responding at http://localhost:8000")
        print("\nStart the server with:")
        print("  cd cli && source venv/bin/activate")
        print("  uvicorn alprina_cli.api.main:app --reload --port 8000")
        sys.exit(1)

    # Run tests
    results = []

    results.append(("Endpoints Registered", test_auth_endpoints_exist()))
    results.append(("OpenAPI Docs", test_openapi_docs()))
    results.append(("Register Endpoint", test_register_endpoint()))
    results.append(("Login Endpoint", test_login_endpoint()))
    results.append(("Protected /me", test_me_endpoint_without_auth()))
    results.append(("Protected /api-keys", test_api_keys_endpoint_without_auth()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} {name}")

    print()
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "=" * 70)
        print("✅ ALL AUTH API TESTS PASSED!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Add SUPABASE_KEY to .env (see GET_SERVICE_ROLE_KEY.md)")
        print("2. Run SQL schema in Supabase")
        print("3. Restart API server")
        print("4. Test full registration flow")
        print()
        print("API Documentation: http://localhost:8000/docs")
        return 0
    else:
        print("\n❌ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
