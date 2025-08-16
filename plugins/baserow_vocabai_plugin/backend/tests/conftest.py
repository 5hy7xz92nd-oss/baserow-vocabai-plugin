from __future__ import print_function

import pytest
from unittest.mock import Mock, patch

# noinspection PyUnresolvedReferences
from baserow.test_utils.pytest_conftest import *  # noqa: F403, F401



@pytest.fixture(autouse=True)
def mock_periodic_field_update_handler():
    """
    this is requried due to the introduction of PeriodicFieldUpdateHandler which attempts to use Redis
    """
    with patch('baserow.contrib.database.fields.periodic_field_update_handler.PeriodicFieldUpdateHandler.mark_workspace_as_recently_used') as mock_mark:
        mock_mark.return_value = None
        yield mock_mark
