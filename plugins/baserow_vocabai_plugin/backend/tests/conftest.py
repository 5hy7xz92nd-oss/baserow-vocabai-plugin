from __future__ import print_function

import pytest
from unittest.mock import Mock, patch

# noinspection PyUnresolvedReferences
from baserow.test_utils.pytest_conftest import *  # noqa: F403, F401


@pytest.fixture(autouse=True)
def mock_redis_for_tests():
    """
    Mock Redis connection for all tests to avoid NotImplementedError.
    This is needed because Baserow's PeriodicFieldUpdateHandler tries to use Redis
    but it's not configured in the test environment.
    """
    with patch('django_redis.get_redis_connection') as mock_get_redis:
        # Create a mock Redis client
        mock_redis_client = Mock()
        mock_redis_client.set.return_value = True
        mock_redis_client.get.return_value = None
        mock_redis_client.delete.return_value = True
        mock_redis_client.exists.return_value = False
        mock_redis_client.expire.return_value = True
        mock_redis_client.ttl.return_value = -1
        mock_redis_client.pipeline.return_value = mock_redis_client
        mock_redis_client.execute.return_value = []
        
        # Make get_redis_connection return our mock
        mock_get_redis.return_value = mock_redis_client
        
        yield mock_redis_client


@pytest.fixture(autouse=True)
def mock_periodic_field_update_handler():
    """
    Alternative approach: directly mock the PeriodicFieldUpdateHandler methods
    that use Redis.
    """
    with patch('baserow.contrib.database.fields.periodic_field_update_handler.PeriodicFieldUpdateHandler.mark_workspace_as_recently_used') as mock_mark:
        mock_mark.return_value = None
        yield mock_mark
