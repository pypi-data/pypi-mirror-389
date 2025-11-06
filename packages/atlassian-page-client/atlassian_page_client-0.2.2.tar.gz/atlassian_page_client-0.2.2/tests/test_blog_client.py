"""Tests for AtlassianBlogClient."""

import json
from unittest.mock import ANY, Mock, patch

import pytest
from requests.auth import HTTPBasicAuth

from atlassian_page_client.blog_client import AtlassianBlogClient


class TestAtlassianBlogClient:
    """Test cases for AtlassianBlogClient class."""

    def test_initialization(self, client_config):
        """Test client initialization."""
        client = AtlassianBlogClient(**client_config)

        assert client.email == client_config["email"]
        assert client.token == client_config["token"]
        assert client.base_url == client_config["base_url"]
        assert isinstance(client.basicAuth, HTTPBasicAuth)
        assert client.HEADERS == {"Content-Type": "application/json;charset=iso-8859-1"}

    def test_check_response_success(self, client_config, mock_requests_response):
        """Test check_response with successful response."""
        client = AtlassianBlogClient(**client_config)
        mock_requests_response.status_code = 200

        # Should not raise an exception
        client.check_response(mock_requests_response)

    def test_check_response_failure(self, client_config, mock_requests_response):
        """Test check_response with failed response."""
        client = AtlassianBlogClient(**client_config)
        mock_requests_response.status_code = 400
        mock_requests_response.text = "Bad Request"

        with pytest.raises(Exception) as exc_info:
            client.check_response(mock_requests_response)

        assert "Failed to get page from url" in str(exc_info.value)
        assert "400" in str(exc_info.value)
        assert "Bad Request" in str(exc_info.value)

    @patch("atlassian_page_client.blog_client.requests.post")
    @patch("atlassian_page_client.blog_client.datetime")
    def test_post_blog_success(
        self, mock_datetime, mock_post, client_config, mock_requests_response
    ):
        """Test successful blog post creation."""
        client = AtlassianBlogClient(**client_config)

        # Mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-11-05"
        mock_datetime.now.return_value = mock_now

        # Setup mock response
        blog_response_data = {
            "id": "67890",
            "status": "current",
            "title": "Test Blog Post",
            "spaceId": "123456",
            "body": {"representation": "storage", "value": "<p>Test blog content</p>"},
        }
        mock_requests_response.status_code = 200
        mock_requests_response.text = json.dumps(blog_response_data)
        mock_post.return_value = mock_requests_response

        # Call the method
        space_id = 123456
        title = "Test Blog Post"
        body = "<p>Test blog content</p>"
        response = client.post(space_id, title, body)

        # Verify the request
        expected_url = client.base_url + "/wiki/api/v2/blogposts"
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[0][0] == expected_url
        assert call_args[1]["headers"] == client.HEADERS
        assert call_args[1]["auth"] == client.basicAuth

        # Verify the data payload
        sent_data = json.loads(call_args[1]["data"])
        assert sent_data["spaceId"] == space_id
        assert sent_data["title"] == title
        assert sent_data["body"]["value"] == body
        assert sent_data["body"]["representation"] == "storage"
        assert sent_data["status"] == "current"
        assert sent_data["createdAt"] == "2025-11-05"

        # Verify the response
        assert response.status_code == 200

    @patch("atlassian_page_client.blog_client.requests.post")
    @patch("atlassian_page_client.blog_client.datetime")
    def test_post_blog_failure(
        self, mock_datetime, mock_post, client_config, mock_requests_response
    ):
        """Test failed blog post creation."""
        client = AtlassianBlogClient(**client_config)

        # Mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-11-05"
        mock_datetime.now.return_value = mock_now

        # Setup mock response for failure
        mock_requests_response.status_code = 403
        mock_requests_response.text = "Forbidden - Insufficient permissions"
        mock_post.return_value = mock_requests_response

        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            client.post(123456, "Test Blog", "<p>Content</p>")

        assert "Failed to get page from url" in str(exc_info.value)
        assert "403" in str(exc_info.value)

    @patch("atlassian_page_client.blog_client.requests.post")
    @patch("atlassian_page_client.blog_client.datetime")
    def test_post_blog_with_complex_html(
        self, mock_datetime, mock_post, client_config, mock_requests_response
    ):
        """Test blog post creation with complex HTML content."""
        client = AtlassianBlogClient(**client_config)

        # Mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-11-05"
        mock_datetime.now.return_value = mock_now

        # Setup mock response
        mock_requests_response.status_code = 200
        mock_requests_response.text = json.dumps({"id": "67890"})
        mock_post.return_value = mock_requests_response

        # Complex HTML content
        complex_body = """
        <h1>Test Header</h1>
        <p>Paragraph with <strong>bold</strong> and <em>italic</em> text.</p>
        <table>
            <tr><td>Cell 1</td><td>Cell 2</td></tr>
        </table>
        <ac:structured-macro ac:name="info">
            <ac:rich-text-body>
                <p>Info macro content</p>
            </ac:rich-text-body>
        </ac:structured-macro>
        """

        # Call the method
        response = client.post(123456, "Complex Blog Post", complex_body)

        # Verify the request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify the complex HTML was included in the payload
        sent_data = json.loads(call_args[1]["data"])
        assert sent_data["body"]["value"] == complex_body
        assert response.status_code == 200

    @patch("atlassian_page_client.blog_client.requests.post")
    @patch("atlassian_page_client.blog_client.datetime")
    def test_post_blog_with_special_characters(
        self, mock_datetime, mock_post, client_config, mock_requests_response
    ):
        """Test blog post creation with special characters in title and body."""
        client = AtlassianBlogClient(**client_config)

        # Mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "2025-11-05"
        mock_datetime.now.return_value = mock_now

        # Setup mock response
        mock_requests_response.status_code = 200
        mock_requests_response.text = json.dumps({"id": "67890"})
        mock_post.return_value = mock_requests_response

        # Title and body with special characters
        title = "Test Blog: Special Characters & Symbols <>"
        body = "<p>Content with special chars: &amp; &lt; &gt; &quot;</p>"

        # Call the method
        response = client.post(123456, title, body)

        # Verify the request was made
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify special characters were preserved
        sent_data = json.loads(call_args[1]["data"])
        assert sent_data["title"] == title
        assert sent_data["body"]["value"] == body
        assert response.status_code == 200

    def test_headers_content_type(self, client_config):
        """Test that headers are properly set with correct content type."""
        client = AtlassianBlogClient(**client_config)

        assert "Content-Type" in client.HEADERS
        assert client.HEADERS["Content-Type"] == "application/json;charset=iso-8859-1"

    def test_basic_auth_credentials(self, client_config):
        """Test that basic auth is properly configured."""
        client = AtlassianBlogClient(**client_config)

        assert isinstance(client.basicAuth, HTTPBasicAuth)
        assert client.basicAuth.username == client_config["email"]
        assert client.basicAuth.password == client_config["token"]
