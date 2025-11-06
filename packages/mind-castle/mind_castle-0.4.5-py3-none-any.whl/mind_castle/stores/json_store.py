# import json
# import logging
# import os
# from mind_castle.secret_store_base import SecretStoreBase

# logger = logging.getLogger(__name__)


# class JsonSecretStore(SecretStoreBase):
#     """
#     An json-file secret store.
#     Use only for testing or development.
#     """

#     store_type = "json"
#     filename = "secrets.json"

#     def __init__(self):
#         if not os.path.exists(self.filename):
#             with open(self.filename, "w") as f:
#                 f.write("{}")

#     def create_secret(self, key: str, value: str) -> dict:
#         with open(self.filename, "r") as f:
#             secrets = json.load(f)
#             secrets[key] = value

#         with open(self.filename, "w") as f:
#             json.dump(secrets, f)
#         return {"mind_castle_secret_type": self.store_type, "key": key}

#     def retrieve_secret(self, secret_details: dict) -> str:
#         key = secret_details.get("key")
#         with open(self.filename, "r") as f:
#             secrets = json.load(f)
#         return secrets.get(key)

#     def update_secret(self, secret_details: dict, value: str) -> dict:
#         return self.create_secret(secret_details.get("key"), value)

#     def delete_secret(self, secret_details: dict) -> None:
#         key = secret_details.get("key")
#         with open(self.filename, "r") as f:
#             secrets = json.load(f)

#         del secrets[key]

#         with open(self.filename, "w") as f:
#             json.dump(secrets, f)
