"""
A Python client library for interacting with Atlassian Confluence pages.

This library provides a simple interface to read and modify Confluence pages
through the Atlassian REST API.
"""

from .attachment_client import AtlassianAttachmentClient
from .blog_client import AtlassianBlogClient
from .client_factory import AtlassianClientFactory
from .page import AtlassianPage
from .page_client import AtlassianPageClient
from .page_content import AtlassianPageContent

__version__ = "0.1.0"
__author__ = "Yannick Zimmermann"
__email__ = "yannick.zimmermann@proton.me"

__all__ = [
    "AtlassianPageClient",
    "AtlassianBlogClient",
    "AtlassianAttachmentClient",
    "AtlassianPage",
    "AtlassianPageContent",
    "AtlassianClientFactory",
]
