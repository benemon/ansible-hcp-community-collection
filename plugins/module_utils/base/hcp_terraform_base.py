import os
import requests
from ansible.errors import AnsibleError

class HCPTerraformBase:
    """Base class for HCP Terraform modules, handling authentication and API requests."""

    def __init__(self, api_token=None, base_url=None):
        """Initialize authentication with a provided API token or environment variable."""
        self.api_token = api_token or os.getenv("TF_API_TOKEN")
        if not self.api_token:
            raise AnsibleError("HCP Terraform API token is required. Set TF_API_TOKEN or provide it explicitly.")

        # Use provided base_url, environment variable, or default to Terraform Cloud
        self.base_url = base_url or os.getenv("TF_BASE_URL", "https://app.terraform.io/api/v2")

    def _get_headers(self):
        """Return authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def _request(self, method, endpoint, data=None):
        """Perform an API request to HCP Terraform with error handling."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        try:
            response = requests.request(method, url, headers=headers, json=data)
            response.raise_for_status()
            return response.json() if response.text else None
        except requests.exceptions.HTTPError as errh:
            raise AnsibleError(f"HTTP Error: {errh.response.status_code} - {errh.response.text}")
        except requests.exceptions.ConnectionError:
            raise AnsibleError("Error: Unable to connect to Terraform API.")
        except requests.exceptions.Timeout:
            raise AnsibleError("Error: Request to Terraform API timed out.")
        except requests.exceptions.RequestException as err:
            raise AnsibleError(f"Unexpected Error: {str(err)}")
