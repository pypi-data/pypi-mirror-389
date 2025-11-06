"""Unit test for DomoCard.Datasets manager (no credentials needed)"""

from dataclasses import dataclass
import domolibrary2.client.auth as dmda
import domolibrary2.classes.DomoCard as dmdc


def test_card_datasets_initialization():
    """Test that CardDatasets is properly initialized"""

    print("=" * 80)
    print("TEST: CardDatasets Initialization")
    print("=" * 80)

    # Create mock auth
    mock_auth = dmda.DomoTokenAuth(
        domo_instance="test-instance",
        domo_access_token="test-token"
    )

    # Create a card manually
    card = dmdc.DomoCard(
        id="card-123",
        auth=mock_auth,
        title="Test Card",
        raw={"datasources": []}
    )

    # Verify Datasets property exists
    assert hasattr(card, "Datasets"), "Card should have Datasets property"
    assert card.Datasets is not None, "Datasets should be initialized"
    assert isinstance(card.Datasets, dmdc.CardDatasets), "Should be CardDatasets instance"

    print("✓ Card has Datasets property")
    print(f"✓ Datasets type: {type(card.Datasets).__name__}")
    print(f"✓ Datasets.parent: {card.Datasets.parent.id}")
    print(f"✓ Datasets.auth: {card.Datasets.auth.domo_instance}")

    # Verify parent reference
    assert card.Datasets.parent == card, "Datasets should reference parent card"
    assert card.Datasets.auth == card.auth, "Datasets should use parent auth"

    print("\n" + "=" * 80)
    print("✓ All initialization tests passed!")
    print("=" * 80)


def test_card_datasets_structure():
    """Test CardDatasets class structure"""

    print("\n" + "=" * 80)
    print("TEST: CardDatasets Structure")
    print("=" * 80)

    # Verify CardDatasets has required methods
    assert hasattr(dmdc.CardDatasets, "get"), "CardDatasets should have get method"

    # Verify it's a dataclass
    assert hasattr(dmdc.CardDatasets, "__dataclass_fields__"), "Should be a dataclass"

    # Check fields
    fields = dmdc.CardDatasets.__dataclass_fields__
    assert "parent" in fields, "Should have parent field"
    assert "auth" in fields, "Should have auth field"

    # Verify it inherits from DomoManager
    from domolibrary2.entities.entities import DomoManager
    assert issubclass(dmdc.CardDatasets, DomoManager), "Should inherit from DomoManager"

    print("✓ CardDatasets has get() method")
    print("✓ CardDatasets is a dataclass")
    print(f"✓ Fields: {list(fields.keys())}")
    print("✓ CardDatasets inherits from DomoManager")

    print("\n" + "=" * 80)
    print("✓ All structure tests passed!")
    print("=" * 80)


def test_card_datasets_export():
    """Test that CardDatasets is exported"""

    print("\n" + "=" * 80)
    print("TEST: CardDatasets Export")
    print("=" * 80)

    # Verify it's in __all__
    assert "CardDatasets" in dmdc.__all__, "CardDatasets should be in __all__"

    # Verify it can be imported
    from domolibrary2.classes.DomoCard import CardDatasets
    assert CardDatasets is dmdc.CardDatasets

    print("✓ CardDatasets in __all__")
    print("✓ CardDatasets can be imported")

    print("\n" + "=" * 80)
    print("✓ All export tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_card_datasets_initialization()
    test_card_datasets_structure()
    test_card_datasets_export()

    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)
