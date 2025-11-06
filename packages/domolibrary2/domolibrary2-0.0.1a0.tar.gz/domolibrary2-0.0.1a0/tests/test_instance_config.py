"""Test DomoInstanceConfig import and usage"""

import domolibrary2.classes.DomoInstanceConfig as dmic
import domolibrary2.client.auth as dmda

# Create test auth
auth = dmda.DomoTokenAuth(
    domo_instance="test-instance",
    domo_access_token="test-token"
)

# Try to instantiate
try:
    ic = dmic.DomoInstanceConfig(auth=auth)
    print("✓ DomoInstanceConfig instantiated")
    print(f"Type: {type(ic)}")
    print(f"Has Publish: {hasattr(ic, 'Publish')}")
    print(f"Attributes: {[attr for attr in dir(ic) if not attr.startswith('_')]}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
