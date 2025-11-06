"""Comprehensive test of DomoCard module structure"""

import domolibrary2.client.auth as dmda
import domolibrary2.classes.DomoCard as dmdc


def test_module_structure():
    """Test that module is properly structured"""

    print("=" * 80)
    print("TEST: Module Structure")
    print("=" * 80)

    # Check __all__ exports
    expected = [
        "DomoCard",
        "DomoCard_Default",
        "FederatedDomoCard",
        "DomoPublishCard",
        "CardDatasets",
        "Card_DownloadSourceCodeError",
    ]

    for name in expected:
        assert name in dmdc.__all__, f"{name} should be in __all__"
        assert hasattr(dmdc, name), f"{name} should be accessible"
        print(f"✓ {name} exported and accessible")

    print("\n" + "=" * 80)
    print("✓ All module structure tests passed!")
    print("=" * 80)


async def test_backwards_compatibility():
    """Test that old import patterns still work"""

    print("\n" + "=" * 80)
    print("TEST: Backwards Compatibility")
    print("=" * 80)

    # Create mock auth
    mock_auth = dmda.DomoTokenAuth(
        domo_instance="test-instance",
        domo_access_token="test-token"
    )

    # Test 1: Can still import and use DomoCard
    card_data = {
        "id": "card-123",
        "title": "Test Card",
        "type": "kpi",
    }

    card = await dmdc.DomoCard.from_dict(auth=mock_auth, obj=card_data)
    assert card.id == "card-123"
    assert card.title == "Test Card"
    print("✓ DomoCard.from_dict() works")

    # Test 2: Can import specific classes
    from domolibrary2.classes.DomoCard import (
        DomoCard,
        DomoCard_Default,
        FederatedDomoCard,
        CardDatasets,
    )

    assert DomoCard is not None
    assert DomoCard_Default is not None
    assert FederatedDomoCard is not None
    assert CardDatasets is not None
    print("✓ Specific class imports work")

    # Test 3: CardDatasets still works
    card_with_datasets = dmdc.DomoCard_Default(
        id="card-456",
        auth=mock_auth,
        raw={},
        Relations=None,
    )
    assert hasattr(card_with_datasets, "Datasets")
    assert isinstance(card_with_datasets.Datasets, CardDatasets)
    print("✓ CardDatasets integration works")

    print("\n" + "=" * 80)
    print("✓ All backwards compatibility tests passed!")
    print("=" * 80)


def test_file_organization():
    """Test that files are properly organized"""

    print("\n" + "=" * 80)
    print("TEST: File Organization")
    print("=" * 80)

    import os

    module_dir = os.path.dirname(dmdc.__file__)

    expected_files = [
        "__init__.py",
        "card_default.py",
        "core.py",
    ]

    for filename in expected_files:
        filepath = os.path.join(module_dir, filename)
        assert os.path.exists(filepath), f"{filename} should exist"
        print(f"✓ {filename} exists")

    # Check that old DomoCard.py is gone
    old_file = os.path.join(os.path.dirname(module_dir), "DomoCard.py")
    assert not os.path.exists(old_file), "Old DomoCard.py should be removed"
    print("✓ Old DomoCard.py removed")

    print("\n" + "=" * 80)
    print("✓ All file organization tests passed!")
    print("=" * 80)


def test_class_locations():
    """Test that classes are in the correct files"""

    print("\n" + "=" * 80)
    print("TEST: Class Locations")
    print("=" * 80)

    # card_default.py classes
    assert dmdc.DomoCard_Default.__module__ == "domolibrary2.classes.DomoCard.card_default"
    print(f"✓ DomoCard_Default in card_default.py")

    assert dmdc.CardDatasets.__module__ == "domolibrary2.classes.DomoCard.card_default"
    print(f"✓ CardDatasets in card_default.py")

    # core.py classes
    assert dmdc.FederatedDomoCard.__module__ == "domolibrary2.classes.DomoCard.core"
    print(f"✓ FederatedDomoCard in core.py")

    assert dmdc.DomoPublishCard.__module__ == "domolibrary2.classes.DomoCard.core"
    print(f"✓ DomoPublishCard in core.py")

    assert dmdc.DomoCard.__module__ == "domolibrary2.classes.DomoCard.core"
    print(f"✓ DomoCard in core.py")

    print("\n" + "=" * 80)
    print("✓ All class location tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio

    test_module_structure()
    asyncio.run(test_backwards_compatibility())
    test_file_organization()
    test_class_locations()

    print("\n" + "=" * 80)
    print("🎉 ALL MODULE TESTS PASSED!")
    print("=" * 80)
