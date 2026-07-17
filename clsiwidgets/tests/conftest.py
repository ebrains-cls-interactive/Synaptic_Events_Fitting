from unittest import mock
import pytest
from clsiwidgets.ui.nsg_credentials_widget import NSGCredentialsWidget


@pytest.fixture
def mocker():
    """
    Small pytest-mock compatible fixture for this test suite.
    """

    class Mocker:
        Mock = mock.Mock
        MagicMock = mock.MagicMock

        def __init__(self):
            self._patchers = []

        def patch(self, *args, **kwargs):
            patcher = mock.patch(*args, **kwargs)
            patched_object = patcher.start()
            self._patchers.append(patcher)
            return patched_object

        def stopall(self):
            for patcher in reversed(self._patchers):
                patcher.stop()

            self._patchers = []

    mocker_fixture = Mocker()

    try:
        yield mocker_fixture
    finally:
        mocker_fixture.stopall()


@pytest.fixture
def nsg_credentials_widget():
    """Create and clean up an NSG credentials widget."""

    widget = NSGCredentialsWidget()

    try:
        yield widget
    finally:
        widget.close()