"""Test improved humanReadable for schedules"""

from domolibrary2.classes.subentity import DomoTriggerSettings

# Test data with cron schedule
test_data = {
    "triggers": [
        {
            "triggerId": 1,
            "title": "Weekly Monday Morning",
            "triggerEvents": [{
                "type": "SCHEDULE",
                "id": "schedule-1",
                "schedule": {
                    "second": "0",
                    "minute": "47",
                    "hour": "12",
                    "dayOfMonth": "?",
                    "month": "*",
                    "dayOfWeek": "MON",
                    "year": "*"
                }
            }],
            "triggerConditions": []
        },
        {
            "triggerId": 2,
            "title": "Daily at 9 AM",
            "triggerEvents": [{
                "type": "SCHEDULE",
                "schedule": {
                    "second": "0",
                    "minute": "0",
                    "hour": "9",
                    "dayOfMonth": "*",
                    "month": "*",
                    "dayOfWeek": "*",
                    "year": "*"
                }
            }],
            "triggerConditions": []
        }
    ],
    "zoneId": "UTC",
    "locale": "en_US"
}

def test_schedule_human_readable():
    """Test that schedule humanReadable shows cron expression"""

    settings = DomoTriggerSettings.from_dict(test_data)

    print("=" * 80)
    print("IMPROVED SCHEDULE DISPLAY")
    print("=" * 80)

    for trigger in settings.triggers:
        print(f"\nTrigger: {trigger.title}")

        exported = trigger.export_as_dict()
        print(f"  humanReadable: {exported['humanReadable']}")

        for event in exported["triggerEvents"]:
            if event["type"] == "SCHEDULE":
                print(f"  Event humanReadable: {event['humanReadable']}")
                print(f"  Cron expression: {event['schedule']['expression']}")

                # Verify they match
                assert event['humanReadable'] == f"Schedule: {event['schedule']['expression']}"
                print("  ✓ humanReadable matches cron expression")

    print("\n" + "=" * 80)
    print("TEST PASSED: humanReadable now shows cron expressions!")
    print("=" * 80)

if __name__ == "__main__":
    test_schedule_human_readable()
