#!/usr/bin/env python3
"""
Test script for webhook server
Simulates GitHub webhook events for testing
"""
import json
import hmac
import hashlib
import requests
import sys
from datetime import datetime

WEBHOOK_URL = "http://localhost:5000/webhook"
WEBHOOK_SECRET = "test_secret_12345"  # Match your .env for testing

def create_signature(payload: str, secret: str) -> str:
    """Create HMAC signature like GitHub does."""
    mac = hmac.new(
        secret.encode('utf-8'),
        msg=payload.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    return f"sha256={mac.hexdigest()}"

def test_pull_request_opened():
    """Test PR opened event."""
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "number": 42,
            "title": "Test: Add new feature",
            "body": "This is a test PR to verify webhook functionality",
            "draft": False,
            "user": {
                "login": "testuser"
            },
            "base": {
                "repo": {
                    "full_name": "cbwinslow/OpenLegislation-local-dev"
                }
            }
        },
        "repository": {
            "full_name": "cbwinslow/OpenLegislation-local-dev",
            "name": "OpenLegislation-local-dev",
            "owner": {
                "login": "cbwinslow"
            }
        }
    }
    
    payload_str = json.dumps(payload)
    signature = create_signature(payload_str, WEBHOOK_SECRET)
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing PR opened event...")
    print(f"   URL: {WEBHOOK_URL}")
    print(f"   Payload: PR #{payload['pull_request']['number']}")
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_health_check():
    """Test health check endpoint."""
    print("\n🏥 Testing health check...")
    try:
        response = requests.get("http://localhost:5000/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_invalid_signature():
    """Test webhook with invalid signature."""
    payload = {"action": "opened", "pull_request": {"number": 1}}
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-Hub-Signature-256": "sha256=invalid_signature",
        "Content-Type": "application/json"
    }
    
    print("\n🔐 Testing invalid signature (should fail)...")
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 403:
            print("   ✅ Correctly rejected invalid signature")
            return True
        else:
            print("   ❌ Should have returned 403")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🚀 Webhook Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Invalid Signature", test_invalid_signature),
        ("PR Opened Event", test_pull_request_opened),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
