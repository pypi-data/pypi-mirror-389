"""Test DomoAccount access management functionality."""

import sys

sys.path.insert(0, "src")


def test_account_default_methods():
    """Test that DomoAccount_Default has access methods."""
    print("\n" + "=" * 80)
    print("TEST: DomoAccount_Default Access Methods")
    print("=" * 80)

    from domolibrary2.classes.DomoAccount.account_default import DomoAccount_Default
    import inspect

    # Check get_access method exists
    assert hasattr(DomoAccount_Default, "get_access"), "Should have get_access method"
    get_access_sig = inspect.signature(DomoAccount_Default.get_access)
    get_access_params = list(get_access_sig.parameters.keys())

    assert "self" in get_access_params
    assert "session" in get_access_params
    assert "debug_api" in get_access_params
    assert "force_refresh" in get_access_params
    assert "debug_num_stacks_to_drop" in get_access_params

    print("✓ get_access() method exists with correct parameters")
    print(f"  Parameters: {get_access_params}")

    # Check share method exists
    assert hasattr(DomoAccount_Default, "share"), "Should have share method"
    share_sig = inspect.signature(DomoAccount_Default.share)
    share_params = list(share_sig.parameters.keys())

    assert "self" in share_params
    assert "user_id" in share_params
    assert "group_id" in share_params
    assert "access_level" in share_params
    assert "session" in share_params
    assert "debug_api" in share_params
    assert "return_raw" in share_params

    print("✓ share() method exists with correct parameters")
    print(f"  Parameters: {share_params}")


def test_oauth_account_methods():
    """Test that DomoAccount_OAuth has access methods."""
    print("\n" + "=" * 80)
    print("TEST: DomoAccount_OAuth Access Methods")
    print("=" * 80)

    from domolibrary2.classes.DomoAccount.account_oauth import DomoAccount_OAuth
    import inspect

    # Check get_access method exists
    assert hasattr(DomoAccount_OAuth, "get_access"), "Should have get_access method"
    get_access_sig = inspect.signature(DomoAccount_OAuth.get_access)
    get_access_params = list(get_access_sig.parameters.keys())

    assert "self" in get_access_params
    assert "session" in get_access_params
    assert "debug_api" in get_access_params
    assert "force_refresh" in get_access_params

    print("✓ get_access() method exists with correct parameters")
    print(f"  Parameters: {get_access_params}")

    # Check share method exists
    assert hasattr(DomoAccount_OAuth, "share"), "Should have share method"
    share_sig = inspect.signature(DomoAccount_OAuth.share)
    share_params = list(share_sig.parameters.keys())

    assert "self" in share_params
    assert "user_id" in share_params
    assert "group_id" in share_params
    assert "access_level" in share_params

    print("✓ share() method exists with correct parameters")
    print(f"  Parameters: {share_params}")


def test_access_field_definition():
    """Test that Access field is defined with repr=False."""
    print("\n" + "=" * 80)
    print("TEST: Access Field Definition")
    print("=" * 80)

    from domolibrary2.classes.DomoAccount.account_default import DomoAccount_Default
    from domolibrary2.classes.DomoAccount.account_oauth import DomoAccount_OAuth
    from dataclasses import fields

    # Check DomoAccount_Default
    default_fields = {f.name: f.repr for f in fields(DomoAccount_Default)}
    assert "Access" in default_fields, "Access field should be present"
    assert not default_fields["Access"], "Access field should have repr=False"
    print("✓ DomoAccount_Default.Access has repr=False")

    # Check DomoAccount_OAuth
    oauth_fields = {f.name: f.repr for f in fields(DomoAccount_OAuth)}
    assert "Access" in oauth_fields, "OAuth Access field should be present"
    assert not oauth_fields["Access"], "OAuth Access field should have repr=False"
    print("✓ DomoAccount_OAuth.Access has repr=False")


def test_access_classes_exist():
    """Test that DomoAccess classes exist."""
    print("\n" + "=" * 80)
    print("TEST: DomoAccess Classes")
    print("=" * 80)

    from domolibrary2.classes.DomoAccount.access import (
        DomoAccess_Account,
        DomoAccess_OAuth,
        Account_AccessRelationship,
    )

    print("✓ DomoAccess_Account class exists")
    print("✓ DomoAccess_OAuth class exists")
    print("✓ DomoAccess_Relation class exists")

    # Check methods
    assert hasattr(
        DomoAccess_Account, "get"
    ), "DomoAccess_Account should have get method"
    assert hasattr(DomoAccess_OAuth, "get"), "DomoAccess_OAuth should have get method"

    print("✓ DomoAccess classes have get() method")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("DOMOACCOUNT ACCESS MANAGEMENT TEST SUITE")
    print("=" * 80)

    try:
        test_account_default_methods()
        test_oauth_account_methods()
        test_access_field_definition()
        test_access_classes_exist()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nSummary:")
        print("  ✅ DomoAccount_Default has get_access() method")
        print("  ✅ DomoAccount_Default has share() method")
        print("  ✅ DomoAccount_OAuth has get_access() method")
        print("  ✅ DomoAccount_OAuth has share() method")
        print("  ✅ Access attribute marked with repr=False in both classes")
        print("  ✅ DomoAccess classes (Account, OAuth, Relation) exist")
        print("  ✅ All methods have correct signatures")

    except AssertionError as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ UNEXPECTED ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
