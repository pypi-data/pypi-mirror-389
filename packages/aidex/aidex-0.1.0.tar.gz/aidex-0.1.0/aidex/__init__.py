"""
Aidex - A template placeholder Python package.

This is a basic template package that can be used as a starting point
for developing Python packages to be published on PyPI.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"


def hello(name: str = "World") -> str:
    """
    Return a greeting message.
    
    Args:
        name: The name to greet. Defaults to "World".
        
    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"


def get_version() -> str:
    """
    Return the current version of the package.
    
    Returns:
        The version string.
    """
    return __version__


__all__ = ["hello", "get_version", "__version__"]