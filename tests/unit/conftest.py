import os
import sys
import logging
import pytest

try:
    import ansible.errors
except ImportError as e:
    print("Ansible import error: %s" % str(e))
    sys.exit(1)

@pytest.fixture(autouse=True)
def configure_logging():
    """Ensure logs appear in pytest output"""
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
