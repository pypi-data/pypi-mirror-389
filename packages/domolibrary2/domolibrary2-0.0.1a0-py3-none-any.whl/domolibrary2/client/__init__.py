"""Client package public API.

Keep this module minimal to avoid circular imports. Individual modules should
import concrete symbols directly from submodules (for example
``from domolibrary2.client.auth import DomoAuth``) rather than relying on
package-level re-exports.

The client modules are still available via dot notation:
- domolibrary2.client.auth
- domolibrary2.client.entities
- etc.
"""

# Intentionally keep the client package API minimal to avoid circular imports.
# Import concrete classes directly from submodules (for example
# ``from domolibrary2.client.auth import DomoAuth``) to avoid circular import problems.

__all__ = []
