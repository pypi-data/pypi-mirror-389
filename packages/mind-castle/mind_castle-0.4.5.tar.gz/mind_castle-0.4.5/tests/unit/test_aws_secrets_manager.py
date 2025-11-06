# from moto import mock_aws
# import pytest

# from mind_castle.stores.aws import AWSSecretsManagerSecretStore
# from mind_castle.exceptions import RetrieveSecretException


# @mock_aws
# def test_create_secret():
#     secret_store = AWSSecretsManagerSecretStore()
#     key = secret_store.get_secret_key()
#     response = secret_store.create_secret(key, "some_secret_value")

#     # Read the secret from AWS directly to check
#     client = secret_store.client  # Use the same auth etc as the store
#     boto_response = client.get_secret_value(SecretId=response["key"])
#     assert boto_response["SecretString"] == "some_secret_value"
#     assert response["mind_castle_secret_type"] == secret_store.store_type


# @mock_aws
# def test_retrieve_secret():
#     secret_store = AWSSecretsManagerSecretStore()
#     # Add secret directly to AWS
#     client = secret_store.client  # Use the same auth etc as the store
#     client.create_secret(Name="some_secret_key", SecretString="some_secret_value")

#     assert (
#         secret_store.retrieve_secret(
#             {"mind_castle_secret_type": "awssecretsstore", "key": "some_secret_key"}
#         )
#         == "some_secret_value"
#     )


# @mock_aws
# def test_delete_secret():
#     secret_store = AWSSecretsManagerSecretStore()
#     # Add secret directly to AWS
#     client = secret_store.client
#     client.delete_secret(SecretId="some_secret_key", ForceDeleteWithoutRecovery=True)
#     client.create_secret(Name="some_secret_key", SecretString="some_secret_value")

#     secret_store.delete_secret(
#         {"mind_castle_secret_type": "awssecretsstore", "key": "some_secret_key"}
#     )

#     with pytest.raises(RetrieveSecretException):
#         secret_store.retrieve_secret(
#             {"mind_castle_secret_type": "awssecretsstore", "key": "some_secret_key"}
#         )


# @mock_aws
# def test_update_secret():
#     secret_store = AWSSecretsManagerSecretStore()
#     # Add secret directly to AWS
#     client = secret_store.client
#     client.delete_secret(SecretId="some_secret_key", ForceDeleteWithoutRecovery=True)
#     client.create_secret(Name="some_secret_key", SecretString="some_secret_value")

#     secret_store.update_secret(
#         {"mind_castle_secret_type": "awssecretsstore", "key": "some_secret_key"},
#         "some_updated_value",
#     )

#     newvalue = secret_store.retrieve_secret(
#         {"mind_castle_secret_type": "awssecretsstore", "key": "some_secret_key"}
#     )
#     assert newvalue == "some_updated_value"
