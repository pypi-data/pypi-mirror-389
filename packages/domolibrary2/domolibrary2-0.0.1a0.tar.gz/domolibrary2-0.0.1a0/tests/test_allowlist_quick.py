"""Quick test runner for allowlist tests"""
import asyncio
import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Set dummy env vars if not set
os.environ.setdefault("DOMO_INSTANCE", "test-instance")
os.environ.setdefault("DOMO_ACCESS_TOKEN", "test-token")

# Import after path is set
import domolibrary2.classes.DomoInstanceConfig.allowlist as allowlist_module
import domolibrary2.client.auth as dmda

print("=" * 60)
print("TESTING: tests/classes/DomoPage/allowlist.py")
print("=" * 60)

# Test 1: Module imports
print("\n✅ Test 1: Module imports successfully")
print(f"   DomoAllowlist class: {allowlist_module.DomoAllowlist}")
print(f"   validate_ip_or_cidr function: {allowlist_module.validate_ip_or_cidr}")

# Test 2: validate_ip_or_cidr function
print("\n📋 Test 2: validate_ip_or_cidr function")
try:
    # Valid IPv4
    result1 = allowlist_module.validate_ip_or_cidr("192.168.1.1")
    assert result1 is True, "Should return True for valid IPv4"
    print("   ✅ Valid IPv4 (192.168.1.1): PASSED")

    # Valid CIDR
    result2 = allowlist_module.validate_ip_or_cidr("10.0.0.0/8")
    assert result2 is True, "Should return True for valid CIDR"
    print("   ✅ Valid CIDR (10.0.0.0/8): PASSED")

    # Invalid IP
    try:
        allowlist_module.validate_ip_or_cidr("not.an.ip.address")
        print("   ❌ Invalid IP should raise ValueError: FAILED")
    except ValueError:
        print("   ✅ Invalid IP raises ValueError: PASSED")

except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Authentication setup
print("\n📋 Test 3: Authentication setup")
try:
    token_auth = dmda.DomoTokenAuth(
        domo_instance=os.environ.get("DOMO_INSTANCE", ""),
        domo_access_token=os.environ.get("DOMO_ACCESS_TOKEN", ""),
    )
    print(f"   ✅ DomoTokenAuth created: {token_auth.domo_instance}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 4: DomoAllowlist instantiation
print("\n📋 Test 4: DomoAllowlist instantiation")
try:
    dmal = allowlist_module.DomoAllowlist(auth=token_auth)
    print(f"   ✅ DomoAllowlist created")
    print(f"   Instance: {dmal.auth.domo_instance}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 5: display_url property
print("\n📋 Test 5: display_url property")
try:
    dmal = allowlist_module.DomoAllowlist(auth=token_auth)
    url = dmal.display_url
    assert isinstance(url, str), "display_url should return a string"
    assert token_auth.domo_instance in url, "URL should contain instance name"
    assert "admin/security" in url, "URL should point to security settings"
    print(f"   ✅ display_url: {url}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test 6: from_dict method
print("\n📋 Test 6: from_dict method")
try:
    test_data = {
        "allowlist": ["192.168.1.1", "10.0.0.0/8"],
        "is_filter_all_traffic_enabled": True,
    }
    dmal = allowlist_module.DomoAllowlist.from_dict(auth=token_auth, obj=test_data)
    assert dmal.allowlist == test_data["allowlist"], "Allowlist should match input"
    assert dmal.is_filter_all_traffic_enabled is True, "Filter setting should match"
    print(f"   ✅ from_dict works correctly")
    print(f"   Allowlist: {dmal.allowlist}")
    print(f"   Filter enabled: {dmal.is_filter_all_traffic_enabled}")
except Exception as e:
    print(f"   ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("SUMMARY: All basic tests completed!")
print("=" * 60)
print("\n⚠️  Note: Integration tests (actual API calls) require:")
print("   - Valid DOMO_INSTANCE environment variable")
print("   - Valid DOMO_ACCESS_TOKEN with admin permissions")
print("\nTo run integration tests:")
print("   pytest tests/classes/DomoPage/allowlist.py -v -m integration")
