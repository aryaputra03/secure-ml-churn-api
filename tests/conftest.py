"""
Pytest configuration file

This file is placed in the tests/ directory to configure pytest options.
"""

import pytest
import os


# Set testing environment variable
os.environ["TESTING"] = "true"


def pytest_addoption(parser):
    """Add custom pytest command line options"""
    parser.addoption(
        "--ci",
        action="store_true",
        default=False,
        help="Run in CI mode (skip slow tests)"
    )
    parser.addoption(
        "--redis",
        action="store_true",
        default=False,
        help="Run Redis tests (requires Redis server)"
    )


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: mark test as slow (skipped in CI mode)"
    )
    config.addinivalue_line(
        "markers", "redis: mark test as requiring Redis"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    # Skip slow tests in CI mode
    if config.getoption("--ci"):
        skip_slow = pytest.mark.skip(reason="Slow test skipped in CI mode")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    # Skip Redis tests if Redis not available or not requested
    if not config.getoption("--redis"):
        skip_redis = pytest.mark.skip(reason="Redis tests skipped (use --redis to enable)")
        for item in items:
            if "redis" in item.keywords:
                item.add_marker(skip_redis)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Disable rate limiting during tests
    os.environ["DISABLE_RATE_LIMIT"] = "true"
    
    yield
    
    # Cleanup
    if "DISABLE_RATE_LIMIT" in os.environ:
        del os.environ["DISABLE_RATE_LIMIT"]