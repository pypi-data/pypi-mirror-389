# from unittest.mock import ANY

# from mind_castle.secret_store_base import SecretStoreBase
# from mind_castle.stores.vault import HashiCorpVaultSecretStore


# def test_put_secret(mocker):
#     secret_store = HashiCorpVaultSecretStore()
#     key = secret_store.get_secret_key()
#     mocker.patch.object(
#         secret_store.client.secrets.kv.v1, "create_or_update_secret", return_value={}
#     )
#     response = secret_store.put_secret(key, "some_secret_value")

#     assert secret_store.client.secrets.kv.v1.create_or_update_secret.called_once_with(
#         secret=dict(path=ANY, secret_value="some_secret_value")
#     )
#     assert response["mind_castle_secret_type"] == secret_store.store_type
#     assert response["key"] is not None


# def test_get_secret(mocker):
#     mock_vault_response = {
#         "data": {
#             "data": {
#                 "secret_value": "some_secret_value",
#             }
#         }
#     }

#     secret_store = HashiCorpVaultSecretStore()
#     mocker.patch.object(
#         secret_store.client.secrets.kv.v1,
#         "read_secret",
#         return_value=mock_vault_response,
#     )
#     response = secret_store.get_secret(
#         {"mind_castle_secret_type": "hashicorpvault", "key": "some_secret_key2"}
#     )

#     assert secret_store.client.secrets.kv.v1.read_secret.called_once_with(
#         path="some_secret_key2"
#     )
#     assert response == "some_secret_value"


# def test_delete_secret(mocker):
#     secret_store = HashiCorpVaultSecretStore()
#     mocker.patch.object(
#         secret_store.client.secrets.kv.v1, "delete_secret", return_value={}
#     )

#     secret_store.delete_secret({"mind_castle_secret_type": "hashicorpvault", "key": "some_secret_key"})
#     assert secret_store.client.secrets.kv.v1.delete_secret.called_once_with(
#         path="some_secret_key"
#     )
