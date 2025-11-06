"""Test federated and published card classes"""

import domolibrary2.client.auth as dmda
import domolibrary2.classes.DomoCard as dmdc


async def test_card_factory():
    """Test that DomoCard.from_dict returns appropriate class"""

    print("=" * 80)
    print("TEST: Card Factory Pattern")
    print("=" * 80)

    # Create mock auth
    mock_auth = dmda.DomoTokenAuth(
        domo_instance="test-instance",
        domo_access_token="test-token"
    )

    # Test 1: Regular card
    regular_card_data = {
        "id": "card-123",
        "title": "Regular Card",
        "type": "kpi",
        "isFederated": False,
    }

    card = await dmdc.DomoCard.from_dict(auth=mock_auth, obj=regular_card_data)
    assert isinstance(card, dmdc.DomoCard_Default), "Regular card should be DomoCard_Default"
    assert not isinstance(card, dmdc.FederatedDomoCard), "Regular card should not be FederatedDomoCard"
    assert card.id == "card-123"
    assert card.title == "Regular Card"
    print(f"✓ Regular card: {type(card).__name__}")

    # Test 2: Federated card
    federated_card_data = {
        "id": "card-456",
        "title": "Federated Card",
        "type": "kpi",
        "isFederated": True,
    }

    fed_card = await dmdc.DomoCard.from_dict(auth=mock_auth, obj=federated_card_data)
    assert isinstance(fed_card, dmdc.FederatedDomoCard), "Federated card should be FederatedDomoCard"
    assert isinstance(fed_card, dmdc.DomoCard_Default), "FederatedDomoCard should inherit from DomoCard_Default"
    assert fed_card.id == "card-456"
    assert fed_card.title == "Federated Card"
    assert fed_card.is_federated == True
    print(f"✓ Federated card: {type(fed_card).__name__}")

    # Test 3: Check _is_federated method
    assert dmdc.DomoCard._is_federated(regular_card_data) == False
    assert dmdc.DomoCard._is_federated(federated_card_data) == True
    print("✓ _is_federated() method works correctly")

    print("\n" + "=" * 80)
    print("✓ All factory tests passed!")
    print("=" * 80)


def test_card_inheritance():
    """Test inheritance hierarchy"""

    print("\n" + "=" * 80)
    print("TEST: Card Inheritance Hierarchy")
    print("=" * 80)

    from domolibrary2.entities.entities import DomoEntity_w_Lineage
    from domolibrary2.entities.entities_federated import DomoFederatedEntity, DomoPublishedEntity

    # Check DomoCard_Default
    assert issubclass(dmdc.DomoCard_Default, DomoEntity_w_Lineage), "DomoCard_Default should inherit from DomoEntity_w_Lineage"
    print("✓ DomoCard_Default inherits from DomoEntity_w_Lineage")

    # Check FederatedDomoCard
    assert issubclass(dmdc.FederatedDomoCard, dmdc.DomoCard_Default), "FederatedDomoCard should inherit from DomoCard_Default"
    assert issubclass(dmdc.FederatedDomoCard, DomoFederatedEntity), "FederatedDomoCard should inherit from DomoFederatedEntity"
    print("✓ FederatedDomoCard inherits from DomoCard_Default and DomoFederatedEntity")

    # Check DomoPublishCard
    assert issubclass(dmdc.DomoPublishCard, dmdc.FederatedDomoCard), "DomoPublishCard should inherit from FederatedDomoCard"
    assert issubclass(dmdc.DomoPublishCard, DomoPublishedEntity), "DomoPublishCard should inherit from DomoPublishedEntity"
    print("✓ DomoPublishCard inherits from FederatedDomoCard and DomoPublishedEntity")

    # Check DomoCard factory
    assert issubclass(dmdc.DomoCard, dmdc.DomoCard_Default), "DomoCard should inherit from DomoCard_Default"
    print("✓ DomoCard inherits from DomoCard_Default")

    print("\n" + "=" * 80)
    print("✓ All inheritance tests passed!")
    print("=" * 80)


def test_card_exports():
    """Test that all classes are exported"""

    print("\n" + "=" * 80)
    print("TEST: Card Exports")
    print("=" * 80)

    expected_exports = [
        "DomoCard_Default",
        "FederatedDomoCard",
        "DomoPublishCard",
        "DomoCard",
        "CardDatasets",
        "Card_DownloadSourceCodeError",
    ]

    for export in expected_exports:
        assert export in dmdc.__all__, f"{export} should be in __all__"
        print(f"✓ {export} exported")

    print("\n" + "=" * 80)
    print("✓ All export tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_card_factory())
    test_card_inheritance()
    test_card_exports()

    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)
