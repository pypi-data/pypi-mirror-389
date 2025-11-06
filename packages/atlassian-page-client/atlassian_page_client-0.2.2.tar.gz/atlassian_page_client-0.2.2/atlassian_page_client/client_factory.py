from .attachment_client import AtlassianAttachmentClient
from .blog_client import AtlassianBlogClient
from .page_client import AtlassianPageClient


class AtlassianClientFactory:

    def __init__(self, email: str, token: str, base_url: str):
        self.base_url = base_url
        self.email = email
        self.token = token

    def createBlogClient(self) -> AtlassianBlogClient:
        return AtlassianBlogClient(self.email, self.token, self.base_url)

    def createAttachmentClient(self) -> AtlassianAttachmentClient:
        return AtlassianAttachmentClient(self.email, self.token, self.base_url)

    def createPageClient(self) -> AtlassianPageClient:
        return AtlassianPageClient(self.email, self.token, self.base_url)
