"""Specialised vertical extension point."""
from vortenix_newsletter.verticals.generic import GenericVertical

class StorageVertical(GenericVertical):
    """Storage-specific implementation can override analysis incrementally."""
