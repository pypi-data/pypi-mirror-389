from moto import mock_aws
import pytest
import boto3
import os
import base64

from mind_castle.stores.aws_kms import AWSKMSSecretStore


@pytest.fixture(scope="module")
def mockaws():
    with mock_aws():
        kms = boto3.client("kms", region_name="us-east-1")
        response = kms.create_key(
            Description="Test Key", KeyUsage="ENCRYPT_DECRYPT", KeySpec="RSA_4096"
        )
        os.environ["MIND_CASTLE_AWS_KMS_KEY_ARN"] = response["KeyMetadata"]["Arn"]
        yield


def test_create_secret(mockaws):
    secret_store = AWSKMSSecretStore()
    response = secret_store.create_secret("some_secret_value")

    client = secret_store.client  # Use the same auth etc as the store
    boto_response = client.decrypt(
        CiphertextBlob=base64.b64decode(response.encrypted_value),
        KeyId=os.environ["MIND_CASTLE_AWS_KMS_KEY_ARN"],
    )
    assert boto_response["Plaintext"].decode("utf-8") == "some_secret_value"
    assert response.mind_castle_secret_type == secret_store.store_type


# TODO: Add tests for bad-path. E.g. invalid key arn, invalid ciphertext


def test_retrieve_secret(mockaws):
    secret_store = AWSKMSSecretStore()
    response = secret_store.create_secret("some_retrievable_value")

    assert secret_store.retrieve_secret(response) == "some_retrievable_value"


def test_delete_secret():
    secret_store = AWSKMSSecretStore()
    secret_store.delete_secret(
        {"mind_castle_secret_type": "awskms", "key": "some_deletable_key"}
    )
    # Just don't throw an error to pass


def test_update_secret():
    secret_store = AWSKMSSecretStore()
    create_response = secret_store.create_secret("some_updatable_value")

    update_response = secret_store.update_secret(create_response, "some_updated_value")

    newvalue = secret_store.retrieve_secret(update_response)
    assert newvalue == "some_updated_value"
