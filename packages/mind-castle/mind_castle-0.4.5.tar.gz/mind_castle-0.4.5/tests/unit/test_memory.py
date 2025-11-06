# from mind_castle.stores.memory import MemorySecretStore


# def test_create_secret():
#     secret_store = MemorySecretStore()
#     response = secret_store.create_secret("some_secret_value")

#     # Just read the memory from this implementation
#     assert secret_store.secrets[response.key].encrypted_value == "some_secret_value"
#     assert response.mind_castle_secret_type == secret_store.store_type


# def test_retrieve_secret():
#     secret_store = MemorySecretStore()
#     response = secret_store.create_secret("some_secret_value")

#     assert secret_store.retrieve_secret(response) == "some_secret_value"


# def test_update_secret():
#     secret_store = MemorySecretStore()

#     response = secret_store.create_secret("some_secret_value")
#     assert secret_store.retrieve_secret(response) == "some_secret_value"

#     response = secret_store.update_secret(response, "some_updated_value")
#     assert secret_store.retrieve_secret(response) == "some_updated_value"


# def test_delete_secret():
#     secret_store = MemorySecretStore()
#     response = secret_store.create_secret("some_secret_value")

#     secret_store.delete_secret(response)
#     # Just read the memory from this implementation
#     assert response.key not in secret_store.secrets
