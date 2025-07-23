import pytest
import requests_mock

@pytest.fixture
def rm():
    with requests_mock.Mocker() as m:
        yield m
