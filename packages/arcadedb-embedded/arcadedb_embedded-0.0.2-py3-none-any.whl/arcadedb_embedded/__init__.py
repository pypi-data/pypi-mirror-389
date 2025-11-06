"""
arcadedb-embedded v0.0.2 - PLACEHOLDER RELEASE

⚠️ DO NOT USE THIS VERSION IN PRODUCTION ⚠️

This is a placeholder release to claim the PyPI namespace.
Please install version 25.10.1 or later for actual functionality.

Example:
    pip install arcadedb-embedded>=25.10.1
"""

__version__ = "0.0.2"
__all__ = ["__version__"]


def _raise_placeholder_error():
    """Raise an error indicating this is a placeholder version."""
    raise RuntimeError(
        "arcadedb-embedded v0.0.2 is a PLACEHOLDER release with no functionality.\n"
        "Please install a production version:\n"
        "  pip install arcadedb-embedded>=25.10.1\n"
        "\n"
        "See: https://github.com/humemai/arcadedb-embedded-python"
    )


# Make any import attempt fail gracefully
class _PlaceholderModule:
    """Placeholder module that raises an error on any attribute access."""
    
    def __getattr__(self, name):
        _raise_placeholder_error()


import sys
# Replace this module with the placeholder
sys.modules[__name__] = _PlaceholderModule()
