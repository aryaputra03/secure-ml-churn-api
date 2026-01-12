import pytest
from src.api.rate_limit import limiter

@pytest.fixture(autouse=True)
def reset_limiter():
    limiter.reset()