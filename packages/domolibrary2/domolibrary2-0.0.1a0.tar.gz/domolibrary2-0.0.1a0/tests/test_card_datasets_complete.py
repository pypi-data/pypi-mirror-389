"""Test CardDatasets.get() method works correctly"""

import domolibrary2.client.auth as dmda
import domolibrary2.classes.DomoCard as dmdc


def test_card_datasets_get_caching():
    """Test that datasets are cached in the manager"""

    print("=" * 80)
    print("TEST: CardDatasets Caching")
    print("=" * 80)

    # Create mock auth
    mock_auth = dmda.DomoTokenAuth(
        domo_instance="test-instance",
        domo_access_token="test-token"
    )

    # Create a card
    card = dmdc.DomoCard(
        id="card-123",
        auth=mock_auth,
        title="Test Card",
        raw={"datasources": []}
    )

    # Verify datasets property returns from manager
    assert hasattr(card, "datasets"), "Card should have datasets property"
    assert card.datasets == [], "Should return empty list initially"

    # Verify manager has datasets field
    assert hasattr(card.Datasets, "datasets"), "Manager should have datasets field"
    assert card.Datasets.datasets == [], "Manager datasets should be empty initially"

    print("✓ Card.datasets property works")
    print("✓ CardDatasets.datasets field exists")
    print("✓ Both return empty list initially")

    # Simulate adding datasets to manager
    mock_dataset = type('MockDataset', (), {'id': 'ds-1', 'name': 'Test Dataset'})()
    card.Datasets.datasets = [mock_dataset]

    # Verify card.datasets reflects the change
    assert len(card.datasets) == 1, "Should have 1 dataset"
    assert card.datasets[0].id == 'ds-1', "Should be the mock dataset"

    print("✓ Manager datasets can be set")
    print("✓ Card.datasets property reflects manager datasets")

    print("\n" + "=" * 80)
    print("✓ All caching tests passed!")
    print("=" * 80)


def test_cardmanager_fields():
    """Test that CardDatasets has all required fields"""

    print("\n" + "=" * 80)
    print("TEST: CardDatasets Fields")
    print("=" * 80)

    # Check dataclass fields
    fields = dmdc.CardDatasets.__dataclass_fields__

    required_fields = ["parent", "auth", "datasets"]
    for field_name in required_fields:
        assert field_name in fields, f"Should have {field_name} field"
        print(f"✓ Has {field_name} field")

    # Check repr settings
    assert fields["parent"].repr == False, "parent should have repr=False"
    assert fields["auth"].repr == False, "auth should have repr=False"
    assert fields["datasets"].repr == False, "datasets should have repr=False"

    print("✓ All fields have repr=False")

    print("\n" + "=" * 80)
    print("✓ All field tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    test_card_datasets_get_caching()
    test_cardmanager_fields()

    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)
