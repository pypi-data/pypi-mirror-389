"""Test/Demo for DomoTriggerSettings"""

import asyncio
import json

# Test data based on the example provided
test_trigger_settings = {
    "triggerSettings": {
        "triggers": [
            {
                "title": "Trigger Title 1",
                "triggerEvents": [
                    {
                        "datasetId": "8ff9ccb8-18f1-4e2e-bf30-b2970fa37872",
                        "triggerOnDataChanged": False,
                        "type": "DATASET_UPDATED",
                    }
                ],
                "triggerConditions": [],
                "triggerId": 1,
            },
            {
                "title": "Trigger Title 2",
                "triggerEvents": [
                    {
                        "id": "1ee1b6b5-8925-44ed-8cbb-b81a7d89a6a7",
                        "schedule": {
                            "second": "0",
                            "minute": "47",
                            "hour": "12",
                            "dayOfMonth": "?",
                            "month": "*",
                            "dayOfWeek": "MON",
                            "year": "*",
                        },
                        "type": "SCHEDULE",
                    }
                ],
                "triggerConditions": [],
                "triggerId": 2,
            },
        ],
        "zoneId": "UTC",
        "locale": "en_US",
    },
}


async def test_trigger_settings_demo():
    """Test DomoTriggerSettings parsing and display"""
    from domolibrary2.classes.subentity import DomoTriggerSettings

    # Parse trigger settings
    trigger_settings = DomoTriggerSettings.from_dict(
        test_trigger_settings["triggerSettings"]
    )

    print("=" * 80)
    print("TRIGGER SETTINGS SUMMARY")
    print("=" * 80)
    print(f"Timezone: {trigger_settings.zone_id}")
    print(f"Locale: {trigger_settings.locale}")
    print(f"Total Triggers: {len(trigger_settings.triggers)}")
    print()

    print("=" * 80)
    print("DETAILED TRIGGER INFORMATION")
    print("=" * 80)

    for i, trigger in enumerate(trigger_settings.triggers, 1):
        print(f"\nTrigger #{i}:")
        print(f"  ID: {trigger.trigger_id}")
        print(f"  Title: {trigger.title}")
        print(f"  Events: {len(trigger.trigger_events)}")
        print(f"  Conditions: {len(trigger.trigger_conditions)}")
        print(f"  Description: {trigger.get_human_readable_description()}")

        for j, event in enumerate(trigger.trigger_events, 1):
            print(f"\n  Event #{j}:")
            print(f"    Type: {event.event_type.value}")
            print(f"    Description: {event.get_human_readable_description()}")

            # Show specific details based on event type
            if hasattr(event, "dataset_id"):
                print(f"    Dataset ID: {event.dataset_id}")
                print(
                    f"    Trigger on Data Changed: {event.trigger_on_data_changed}"
                )

            if hasattr(event, "schedule") and event.schedule:
                print(f"    Schedule: {event.schedule.get_human_readable_schedule()}")

    print("\n" + "=" * 80)
    print("SUMMARY BY TYPE")
    print("=" * 80)

    schedule_triggers = trigger_settings.get_schedule_triggers()
    dataset_triggers = trigger_settings.get_dataset_triggers()

    print(f"Schedule-based triggers: {len(schedule_triggers)}")
    for trigger in schedule_triggers:
        print(f"  - {trigger.title}")

    print(f"\nDataset-based triggers: {len(dataset_triggers)}")
    for trigger in dataset_triggers:
        print(f"  - {trigger.title}")

    print("\n" + "=" * 80)
    print("HUMAN READABLE SUMMARY")
    print("=" * 80)
    print(trigger_settings.get_human_readable_summary())

    print("\n" + "=" * 80)
    print("SERIALIZATION TEST")
    print("=" * 80)

    # Test round-trip serialization
    serialized = trigger_settings.to_dict()
    print(json.dumps(serialized, indent=2))

    # Parse it back
    trigger_settings_2 = DomoTriggerSettings.from_dict(serialized)
    print(f"\nRound-trip successful: {len(trigger_settings_2.triggers)} triggers parsed")

    return trigger_settings


if __name__ == "__main__":
    asyncio.run(test_trigger_settings_demo())
