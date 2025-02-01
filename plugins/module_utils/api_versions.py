API_VERSIONS = {
    "hvs": "2023-11-28",
    "packer": "2023-01-01",
}

def get_api_version(service_name):
    """Return the API version for the given service, or raise an error if unknown."""
    if service_name not in API_VERSIONS:
        raise ValueError(f"Unknown service '{service_name}', no API version available. "
                         f"Known services: {', '.join(API_VERSIONS.keys())}")
    return API_VERSIONS[service_name]
