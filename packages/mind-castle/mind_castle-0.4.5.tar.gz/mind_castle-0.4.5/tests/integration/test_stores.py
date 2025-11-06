from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import pytest
import logging
from moto import mock_aws
import os
import base64
import math

from hypothesis import given
from hypothesis_jsonschema import from_schema

os.environ["MIND_CASTLE_LOCAL_ENCRYPTION_SECRET"] = base64.urlsafe_b64encode(
    os.urandom(16)
).decode()

from mind_castle.stores import retrieve_secret
from mind_castle.exceptions import RetrieveSecretException
from models import (
    Base,
    SimpleNoneModel,
    SimpleLocalEncryptionModel,
)

logger = logging.getLogger(__name__)

# TEST_STORES = [SimpleMemoryModel, SimpleAWSSecretsManagerModel, SimpleAWSKMSModel, SimpleJsonModel, SimpleLocalEncryptionModel]
TEST_STORES = [SimpleNoneModel, SimpleLocalEncryptionModel]


# Create an in-memory SQLite database
engine = create_engine("sqlite://", echo=True)
Base.metadata.create_all(engine)

session = Session(engine)

mock = mock_aws()
mock.start()


@pytest.mark.parametrize("model", TEST_STORES)
@given(from_schema({}, allow_x00=False, codec="utf-8"))
def test_create_retrieve_secret_values(model, secret_data):
    test_object = model(data=secret_data)
    session.add(test_object)
    session.commit()
    session.expire_all()  # Get rid of cache

    item = session.get(model, test_object.id)
    if isinstance(secret_data, float):
        assert math.isclose(item.data, secret_data)
    else:
        assert item.data == secret_data


@pytest.mark.parametrize("model", TEST_STORES)
@given(
    from_schema({}, allow_x00=False, codec="utf-8"),
    from_schema({}, allow_x00=False, codec="utf-8"),
)
def test_update_secret_values(model, secret_data, updated_data):
    test_object = model(data=secret_data)
    session.add(test_object)
    session.commit()
    session.expire_all()  # Get rid of cache

    # Update the value
    test_object.data = updated_data
    session.commit()
    session.expire_all()  # Get rid of cache

    test_object = session.get(model, test_object.id)
    assert test_object.data == updated_data
    # Decided to create new secrets on update for now, see comments in _track_secret_changes()
    # assert test_object.data._self_secret_details["key"] == key_before


@pytest.mark.parametrize("model", TEST_STORES)
@given(from_schema({}, allow_x00=False, codec="utf-8"))
def test_delete_secret_values(model, secret_data):
    test_object = model(data=secret_data)
    session.add(test_object)
    session.commit()
    session.expire_all()  # Get rid of cache

    # Delete the object
    session.delete(test_object)
    session.commit()
    session.expire_all()  # Get rid of cache

    assert not session.get(model, test_object.id)

    # None is a valid value that's output to shortcut encrypting nothing
    # Local storage store types (KMS etc) wont throw an error here
    if test_object.data and model not in [SimpleLocalEncryptionModel, SimpleNoneModel]:
        with pytest.raises(RetrieveSecretException):
            retrieve_secret(test_object.data._self_secret_details)
