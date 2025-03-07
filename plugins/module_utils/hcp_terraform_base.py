#!/usr/bin/python
import os
import requests
import sys
import time
import random
from ansible.module_utils.basic import AnsibleModule

class HCPTerraformBase(AnsibleModule):
    """
    Base class for HCP Terraform modules.
    Extends AnsibleModule to handle authentication and common API request logic.
    """
    def __init__(self, argument_spec, **kwargs):
        # Initialize the AnsibleModule
        super().__init__(argument_spec=argument_spec, **kwargs)
        self.token = self.params.get('token') or os.getenv("TFE_TOKEN")
        if not self.token:
            self.fail_json(msg="HCP Terraform API token is required. Set TFE_TOKEN or provide it explicitly.")
        self.base_url = self.params.get('base_url') or os.getenv("TF_BASE_URL", "https://app.terraform.io/api/v2")
        
        # Warn macOS users about fork()-related issues.
        if sys.platform == 'darwin' and 'OBJC_DISABLE_INITIALIZE_FORK_SAFETY' not in os.environ:
            sys.stderr.write(
                "WARNING: On macOS, you may need to set OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES "
                "if you encounter fork()-related crashes\n"
            )

    def _get_headers(self):
        """
        Return authentication headers for API requests.
        """
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/vnd.api+json"
        }

    def _request(self, method, endpoint, data=None, params=None, max_retries=10):
        """
        Perform an API request to HCP Terraform with exponential backoff.
        """
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        base_delay = 2
        max_delay = 64

        for attempt in range(max_retries):
            try:
                response = requests.request(method, url, headers=headers, json=data, params=params)
                if response.status_code == 429:
                    if attempt == max_retries - 1:
                        raise Exception("Maximum retry attempts reached for rate limit (429 Too Many Requests).")
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except (ValueError, TypeError):
                            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    else:
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    sys.stderr.write(
                        f"WARNING: Rate limit exceeded. Retrying in {delay:.2f} seconds (attempt {attempt+1}/{max_retries})\n"
                    )
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                return response.json() if response.text else None

            except requests.exceptions.HTTPError as errh:
                status_code = errh.response.status_code
                if status_code in [500, 503, 408] and attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    sys.stderr.write(
                        f"WARNING: Received {status_code}. Retrying in {delay:.2f} seconds (attempt {attempt+1}/{max_retries})\n"
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise Exception(f"HTTP Error: {status_code} - {errh.response.text}")
            except requests.exceptions.ConnectionError:
                raise Exception("Error: Unable to connect to Terraform API.")
            except requests.exceptions.Timeout:
                raise Exception("Error: Request to Terraform API timed out.")
            except requests.exceptions.RequestException as err:
                raise Exception(f"Error making request to Terraform API: {str(err)}")

        raise Exception(f"Terraform API request to {url} failed after {max_retries} retries.")
