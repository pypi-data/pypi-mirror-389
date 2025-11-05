"""Tests for AtlassianAttachmentClient."""

import os
import tempfile
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
from requests.auth import HTTPBasicAuth

from atlassian_page_client.attachment_client import AtlassianAttachmentClient


class TestAtlassianAttachmentClient:
    """Test cases for AtlassianAttachmentClient class."""

    def test_initialization(self, client_config):
        """Test client initialization."""
        client = AtlassianAttachmentClient(**client_config)

        assert client.email == client_config["email"]
        assert client.token == client_config["token"]
        assert client.base_url == client_config["base_url"]
        assert isinstance(client.basicAuth, HTTPBasicAuth)
        assert client.HEADERS == {"X-Atlassian-Token": "no-check"}

    def test_check_response_success(self, client_config, mock_requests_response):
        """Test check_response with successful response."""
        client = AtlassianAttachmentClient(**client_config)
        mock_requests_response.status_code = 200

        # Should not raise an exception
        client.check_response(mock_requests_response)

    def test_check_response_failure(self, client_config, mock_requests_response):
        """Test check_response with failed response."""
        client = AtlassianAttachmentClient(**client_config)
        mock_requests_response.status_code = 413
        mock_requests_response.text = "Request Entity Too Large"

        with pytest.raises(Exception) as exc_info:
            client.check_response(mock_requests_response)

        assert "Failed to get page from url" in str(exc_info.value)
        assert "413" in str(exc_info.value)
        assert "Request Entity Too Large" in str(exc_info.value)

    @patch("atlassian_page_client.attachment_client.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake file content")
    def test_post_attachment_success(
        self, mock_file, mock_post, client_config, mock_requests_response
    ):
        """Test successful attachment upload."""
        client = AtlassianAttachmentClient(**client_config)

        # Setup mock response
        attachment_response_data = {
            "id": "att12345",
            "type": "attachment",
            "title": "test_file.txt",
            "version": {"number": 1},
        }
        mock_requests_response.status_code = 200
        mock_requests_response.text = str(attachment_response_data)
        mock_post.return_value = mock_requests_response

        # Call the method
        blogpost_id = 67890
        file_path = "/path/to/test_file.txt"
        response = client.post(blogpost_id, file_path)

        # Verify the file was opened
        mock_file.assert_called_once_with(file_path, "rb")

        # Verify the request
        expected_url = (
            client.base_url + f"/wiki/rest/api/content/{blogpost_id}/child/attachment"
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        assert call_args[0][0] == expected_url
        assert call_args[1]["headers"] == client.HEADERS
        assert call_args[1]["auth"] == client.basicAuth
        assert "files" in call_args[1]

        # Verify the response
        assert response.status_code == 200

    @patch("atlassian_page_client.attachment_client.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake file content")
    def test_post_attachment_failure(
        self, mock_file, mock_post, client_config, mock_requests_response
    ):
        """Test failed attachment upload."""
        client = AtlassianAttachmentClient(**client_config)

        # Setup mock response for failure
        mock_requests_response.status_code = 404
        mock_requests_response.text = "Blog post not found"
        mock_post.return_value = mock_requests_response

        # Should raise an exception
        with pytest.raises(Exception) as exc_info:
            client.post(99999, "/path/to/test_file.txt")

        assert "Failed to get page from url" in str(exc_info.value)
        assert "404" in str(exc_info.value)

    @patch("atlassian_page_client.attachment_client.requests.post")
    def test_post_attachment_file_not_found(self, mock_post, client_config):
        """Test attachment upload when file doesn't exist."""
        client = AtlassianAttachmentClient(**client_config)

        # Try to upload a non-existent file
        with pytest.raises(FileNotFoundError):
            client.post(67890, "/path/to/nonexistent_file.txt")

        # Verify post was never called
        mock_post.assert_not_called()

    @patch("atlassian_page_client.attachment_client.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"binary image data")
    def test_post_image_attachment(
        self, mock_file, mock_post, client_config, mock_requests_response
    ):
        """Test uploading an image attachment."""
        client = AtlassianAttachmentClient(**client_config)

        # Setup mock response
        mock_requests_response.status_code = 200
        mock_requests_response.text = '{"id": "att12345", "title": "image.png"}'
        mock_post.return_value = mock_requests_response

        # Call the method with an image file
        blogpost_id = 67890
        file_path = "/path/to/image.png"
        response = client.post(blogpost_id, file_path)

        # Verify the file was opened in binary mode
        mock_file.assert_called_once_with(file_path, "rb")

        # Verify the request was made
        mock_post.assert_called_once()
        assert response.status_code == 200

    @patch("atlassian_page_client.attachment_client.requests.post")
    @patch(
        "builtins.open", new_callable=mock_open, read_data=b"large file content" * 1000
    )
    def test_post_large_attachment(
        self, mock_file, mock_post, client_config, mock_requests_response
    ):
        """Test uploading a large attachment."""
        client = AtlassianAttachmentClient(**client_config)

        # Setup mock response
        mock_requests_response.status_code = 200
        mock_requests_response.text = '{"id": "att12345"}'
        mock_post.return_value = mock_requests_response

        # Call the method with a large file
        blogpost_id = 67890
        file_path = "/path/to/large_file.zip"
        response = client.post(blogpost_id, file_path)

        # Verify the request was made
        mock_post.assert_called_once()
        assert response.status_code == 200

    def test_headers_atlassian_token(self, client_config):
        """Test that headers are properly set with X-Atlassian-Token."""
        client = AtlassianAttachmentClient(**client_config)

        assert "X-Atlassian-Token" in client.HEADERS
        assert client.HEADERS["X-Atlassian-Token"] == "no-check"

    def test_basic_auth_credentials(self, client_config):
        """Test that basic auth is properly configured."""
        client = AtlassianAttachmentClient(**client_config)

        assert isinstance(client.basicAuth, HTTPBasicAuth)
        assert client.basicAuth.username == client_config["email"]
        assert client.basicAuth.password == client_config["token"]

    @patch("atlassian_page_client.attachment_client.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"test content")
    def test_post_attachment_with_special_chars_in_filename(
        self, mock_file, mock_post, client_config, mock_requests_response
    ):
        """Test uploading attachment with special characters in filename."""
        client = AtlassianAttachmentClient(**client_config)

        # Setup mock response
        mock_requests_response.status_code = 200
        mock_requests_response.text = '{"id": "att12345"}'
        mock_post.return_value = mock_requests_response

        # Call the method with a filename containing special characters
        blogpost_id = 67890
        file_path = "/path/to/test file (1) [copy].txt"
        response = client.post(blogpost_id, file_path)

        # Verify the file was opened
        mock_file.assert_called_once_with(file_path, "rb")

        # Verify the request was made
        mock_post.assert_called_once()
        assert response.status_code == 200

    @patch("atlassian_page_client.attachment_client.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"")
    def test_post_empty_file(
        self, mock_file, mock_post, client_config, mock_requests_response
    ):
        """Test uploading an empty file."""
        client = AtlassianAttachmentClient(**client_config)

        # Setup mock response
        mock_requests_response.status_code = 200
        mock_requests_response.text = '{"id": "att12345"}'
        mock_post.return_value = mock_requests_response

        # Call the method with an empty file
        blogpost_id = 67890
        file_path = "/path/to/empty_file.txt"
        response = client.post(blogpost_id, file_path)

        # Verify the request was made even for empty file
        mock_post.assert_called_once()
        assert response.status_code == 200

    @patch("atlassian_page_client.attachment_client.requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"test content")
    def test_post_attachment_api_url_format(
        self, mock_file, mock_post, client_config, mock_requests_response
    ):
        """Test that the API URL is correctly formatted."""
        client = AtlassianAttachmentClient(**client_config)

        # Setup mock response
        mock_requests_response.status_code = 200
        mock_requests_response.text = '{"id": "att12345"}'
        mock_post.return_value = mock_requests_response

        # Call the method
        blogpost_id = 12345
        file_path = "/path/to/test.txt"
        client.post(blogpost_id, file_path)

        # Verify the URL format
        expected_url = (
            f"{client.base_url}/wiki/rest/api/content/{blogpost_id}/child/attachment"
        )
        call_args = mock_post.call_args
        assert call_args[0][0] == expected_url
