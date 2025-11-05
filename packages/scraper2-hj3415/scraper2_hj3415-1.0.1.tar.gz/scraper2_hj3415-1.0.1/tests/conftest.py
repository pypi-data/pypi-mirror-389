# test/conftest.py

import pytest
from logging_hj3415 import setup_logging

@pytest.fixture(scope="session", autouse=True)
def logger():
    setup_logging("scraper2_hj3415", level="INFO")
