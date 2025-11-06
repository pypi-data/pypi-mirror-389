# Call JIRA API with HTTPBasicAuth
import json
from datetime import datetime

import requests
from requests.auth import HTTPBasicAuth


class AtlassianBlogClient:
    HEADERS = {"Content-Type": "application/json;charset=iso-8859-1"}

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

    def post(self, space_id: int, title: str, body: str) -> requests.Response:
        apiUrl = f"/wiki/api/v2/blogposts"

        d = {
            "spaceId": space_id,
            "status": "current",
            "title": title,
            "body": {"representation": "storage", "value": body},
            "createdAt": datetime.now().strftime("%Y-%m-%d"),
        }

        data = json.dumps(d)

        response = requests.post(
            self.base_url + apiUrl, headers=self.HEADERS, auth=self.basicAuth, data=data
        )

        self.check_response(response)

        return response
