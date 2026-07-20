"""JobberClientConfig round-trip and validation."""

import pytest
from pydantic import ValidationError

from jobber_graphql_client.config import JobberClientConfig


def test_round_trip(config):
    dumped = config.model_dump()
    rebuilt = JobberClientConfig.model_validate(dumped)
    assert rebuilt == config
    assert rebuilt.model_dump() == dumped


def test_endpoint_default():
    cfg = JobberClientConfig(
        jobber_api_version="2025-04-16",
        jobber_client_id="cid",
        jobber_client_secret="secret",
        jobber_redirect_uri="https://example.test/cb",
        keyring_service_name="svc",
        scopes=["clients:read"],
    )
    assert cfg.jobber_api_endpoint == "https://api.getjobber.com/api/graphql"


@pytest.mark.parametrize(
    "missing",
    [
        "jobber_api_version",
        "jobber_client_id",
        "jobber_client_secret",
        "jobber_redirect_uri",
        "keyring_service_name",
        "scopes",
    ],
)
def test_required_fields(missing, config):
    data = config.model_dump()
    del data[missing]
    with pytest.raises(ValidationError):
        JobberClientConfig.model_validate(data)
