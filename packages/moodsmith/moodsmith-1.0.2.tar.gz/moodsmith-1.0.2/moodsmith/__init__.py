"""Exports functions we want users to import"""

from importlib.metadata import version

from .core import funny, motivational, negative, positive

# imported functions
__all__ = ["positive", "motivational", "negative", "funny"]
__version__ = version("moodsmith")  # package's current version
