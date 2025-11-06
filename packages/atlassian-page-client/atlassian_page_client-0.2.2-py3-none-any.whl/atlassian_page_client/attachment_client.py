# Call JIRA API with HTTPBasicAuth
import requests
from requests.auth import HTTPBasicAuth


class AtlassianAttachmentClient:
    HEADERS = {"X-Atlassian-Token": "no-check"}

    def __init__(self, email: str, token: str, base_url: str):
        self.base_url = base_url
        self.email = email
        self.token = token
        self.basicAuth = HTTPBasicAuth(self.email, self.token)

    def check_response(self, response: requests.Response) -> None:
        if response.status_code != 200:
            raise Exception(
                f"Failed to get page from url {response.url}: {response.status_code} {response.text}"
            )

    def post(self, blogpost_id: int, file_path: str) -> requests.Response:
        apiUrl = f"/wiki/rest/api/content/{blogpost_id}/child/attachment"

        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}

            response = requests.post(
                self.base_url + apiUrl,
                headers=self.HEADERS,
                auth=self.basicAuth,
                files=files,
            )

        self.check_response(response)

        return response
