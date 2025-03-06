import os
import requests
import sys
import json
import time
import random
from ansible.errors import AnsibleError
from ansible.utils.display import Display

display = Display()

class HCPTerraformBase:
    """Base class for HCP Terraform modules, handling authentication and API requests."""

    def __init__(self, token=None, base_url=None):
        """Initialize authentication with a provided API token or environment variable."""
        self.token = token or os.getenv("TFE_TOKEN")
        if not self.token:
            raise AnsibleError("HCP Terraform API token is required. Set TFE_TOKEN or provide it explicitly.")

        # Use provided base_url, environment variable, or default to Terraform Cloud
        self.base_url = base_url or os.getenv("TF_BASE_URL", "https://app.terraform.io/api/v2")

        # Warn macOS users about potential fork() safety issues
        if sys.platform == 'darwin' and 'OBJC_DISABLE_INITIALIZE_FORK_SAFETY' not in os.environ:
            display.warning(
                'On macOS, you may need to set OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES '
                'if you encounter fork()-related crashes'
            )

    def _get_headers(self):
        """Return authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def _request(self, method, endpoint, data=None, params=None, max_retries=10):
        """Perform an API request to HCP Terraform with exponential backoff."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        base_delay = 2  # Initial backoff time in seconds
        max_delay = 64  # Maximum delay time in seconds

        for attempt in range(max_retries):
            try:
                display.vvv(f"Making {method} request to {url}")
                if data:
                    display.vvv(f"With data: {json.dumps(data, indent=2)}")
                if params:
                    display.vvv(f"With parameters: {json.dumps(params, indent=2)}")

                response = requests.request(method, url, headers=headers, json=data, params=params)
                display.vvv(f"Response status code: {response.status_code}")

                if response.status_code == 429:
                    if attempt == max_retries - 1:
                        raise AnsibleError(f"Maximum retry attempts reached for rate limit (429 Too Many Requests).")

                    # Respect Retry-After header if present
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except (ValueError, TypeError):
                            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    else:
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)

                    display.warning(f"Rate limit exceeded. Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue

                # Raise exception for HTTP errors
                response.raise_for_status()

                # Return raw API response
                return response.json() if response.text else None

            except requests.exceptions.HTTPError as errh:
                status_code = errh.response.status_code

                # Retry on transient errors (500, 503, 408)
                if status_code in [500, 503, 408] and attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    display.warning(f"Received {status_code}. Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise AnsibleError(f"HTTP Error: {status_code} - {errh.response.text}")

            except requests.exceptions.ConnectionError:
                raise AnsibleError("Error: Unable to connect to Terraform API.")

            except requests.exceptions.Timeout:
                raise AnsibleError("Error: Request to Terraform API timed out.")

            except requests.exceptions.RequestException as err:
                raise AnsibleError(f"Error making request to Terraform API: {str(err)}")

        # If all retries fail, return an error
        raise AnsibleError(f"Terraform API request to {url} failed after {max_retries} retries.")
