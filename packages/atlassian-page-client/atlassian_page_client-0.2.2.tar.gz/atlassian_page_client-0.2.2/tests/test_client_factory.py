"""Tests for AtlassianClientFactory."""

import pytest

from atlassian_page_client.attachment_client import AtlassianAttachmentClient
from atlassian_page_client.blog_client import AtlassianBlogClient
from atlassian_page_client.client_factory import AtlassianClientFactory
from atlassian_page_client.page_client import AtlassianPageClient


class TestAtlassianClientFactory:
    """Test cases for AtlassianClientFactory class."""

    def test_initialization(self, client_config):
        """Test factory initialization."""
        factory = AtlassianClientFactory(**client_config)

        assert factory.email == client_config["email"]
        assert factory.token == client_config["token"]
        assert factory.base_url == client_config["base_url"]

    def test_create_blog_client(self, client_config):
        """Test creating a blog client."""
        factory = AtlassianClientFactory(**client_config)

        blog_client = factory.createBlogClient()

        assert isinstance(blog_client, AtlassianBlogClient)
        assert blog_client.email == client_config["email"]
        assert blog_client.token == client_config["token"]
        assert blog_client.base_url == client_config["base_url"]

    def test_create_attachment_client(self, client_config):
        """Test creating an attachment client."""
        factory = AtlassianClientFactory(**client_config)

        attachment_client = factory.createAttachmentClient()

        assert isinstance(attachment_client, AtlassianAttachmentClient)
        assert attachment_client.email == client_config["email"]
        assert attachment_client.token == client_config["token"]
        assert attachment_client.base_url == client_config["base_url"]

    def test_create_page_client(self, client_config):
        """Test creating a page client."""
        factory = AtlassianClientFactory(**client_config)

        page_client = factory.createPageClient()

        assert isinstance(page_client, AtlassianPageClient)
        assert page_client.email == client_config["email"]
        assert page_client.token == client_config["token"]
        assert page_client.base_url == client_config["base_url"]

    def test_create_multiple_clients(self, client_config):
        """Test creating multiple different clients from the same factory."""
        factory = AtlassianClientFactory(**client_config)

        blog_client = factory.createBlogClient()
        attachment_client = factory.createAttachmentClient()
        page_client = factory.createPageClient()

        # Verify all clients are created and are different instances
        assert isinstance(blog_client, AtlassianBlogClient)
        assert isinstance(attachment_client, AtlassianAttachmentClient)
        assert isinstance(page_client, AtlassianPageClient)

        # Verify they all share the same configuration
        for client in [blog_client, attachment_client, page_client]:
            assert client.email == client_config["email"]
            assert client.token == client_config["token"]
            assert client.base_url == client_config["base_url"]

    def test_create_multiple_instances_of_same_client(self, client_config):
        """Test creating multiple instances of the same client type."""
        factory = AtlassianClientFactory(**client_config)

        blog_client1 = factory.createBlogClient()
        blog_client2 = factory.createBlogClient()

        # Verify they are separate instances
        assert blog_client1 is not blog_client2

        # But have the same configuration
        assert blog_client1.email == blog_client2.email
        assert blog_client1.token == blog_client2.token
        assert blog_client1.base_url == blog_client2.base_url

    def test_factory_with_different_base_urls(self):
        """Test factory with different base URLs."""
        config1 = {
            "email": "test1@example.com",
            "token": "token1",
            "base_url": "https://site1.atlassian.net",
        }
        config2 = {
            "email": "test2@example.com",
            "token": "token2",
            "base_url": "https://site2.atlassian.net",
        }

        factory1 = AtlassianClientFactory(**config1)
        factory2 = AtlassianClientFactory(**config2)

        client1 = factory1.createPageClient()
        client2 = factory2.createPageClient()

        assert client1.base_url == config1["base_url"]
        assert client2.base_url == config2["base_url"]
        assert client1.base_url != client2.base_url

    def test_factory_with_empty_credentials(self):
        """Test factory with empty credentials."""
        config = {"email": "", "token": "", "base_url": ""}

        factory = AtlassianClientFactory(**config)

        # Factory should still create clients, even with empty credentials
        blog_client = factory.createBlogClient()

        assert isinstance(blog_client, AtlassianBlogClient)
        assert blog_client.email == ""
        assert blog_client.token == ""
        assert blog_client.base_url == ""

    def test_factory_preserves_credentials_across_clients(self, client_config):
        """Test that factory preserves credentials across all created clients."""
        factory = AtlassianClientFactory(**client_config)

        # Create all client types
        blog_client = factory.createBlogClient()
        attachment_client = factory.createAttachmentClient()
        page_client = factory.createPageClient()

        # Verify all clients have the same credentials
        clients = [blog_client, attachment_client, page_client]
        for client in clients:
            assert client.email == client_config["email"]
            assert client.token == client_config["token"]
            assert client.base_url == client_config["base_url"]

    def test_factory_client_headers(self, client_config):
        """Test that clients created by factory have correct headers."""
        factory = AtlassianClientFactory(**client_config)

        blog_client = factory.createBlogClient()
        attachment_client = factory.createAttachmentClient()
        page_client = factory.createPageClient()

        # Verify headers are set correctly for each client type
        assert blog_client.HEADERS == {
            "Content-Type": "application/json;charset=iso-8859-1"
        }
        assert attachment_client.HEADERS == {"X-Atlassian-Token": "no-check"}
        assert page_client.HEADERS == {
            "Content-Type": "application/json;charset=iso-8859-1"
        }

    def test_factory_client_basic_auth(self, client_config):
        """Test that clients created by factory have basic auth configured."""
        factory = AtlassianClientFactory(**client_config)

        blog_client = factory.createBlogClient()
        attachment_client = factory.createAttachmentClient()
        page_client = factory.createPageClient()

        # Verify basic auth is configured for all clients
        for client in [blog_client, attachment_client, page_client]:
            assert hasattr(client, "basicAuth")
            assert client.basicAuth.username == client_config["email"]
            assert client.basicAuth.password == client_config["token"]

    def test_factory_method_naming_convention(self, client_config):
        """Test that factory methods follow naming convention."""
        factory = AtlassianClientFactory(**client_config)

        # Verify method names exist and are callable
        assert hasattr(factory, "createBlogClient")
        assert callable(factory.createBlogClient)

        assert hasattr(factory, "createAttachmentClient")
        assert callable(factory.createAttachmentClient)

        assert hasattr(factory, "createPageClient")
        assert callable(factory.createPageClient)

    def test_factory_with_special_characters_in_credentials(self):
        """Test factory with special characters in credentials."""
        config = {
            "email": "test+user@example.com",
            "token": "token_with_special_chars!@#$%",
            "base_url": "https://my-site.atlassian.net",
        }

        factory = AtlassianClientFactory(**config)

        page_client = factory.createPageClient()

        assert page_client.email == config["email"]
        assert page_client.token == config["token"]
        assert page_client.base_url == config["base_url"]
