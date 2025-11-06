# import logging

# from mind_castle.secret_store_base import SecretStoreBase, MindCastleSecret

# logger = logging.getLogger(__name__)


# class MemorySecretStore(SecretStoreBase):
#     """
#     An in-memory secret store.
#     This is not persistent and will be lost when the application is restarted.
#     Use only for testing or development.
#     """

#     store_type = "memory"

#     def __init__(self):
#         self.secrets = {}

#     def create_secret(self, value: str) -> MindCastleSecret:
#         secret = MindCastleSecret(
#             mind_castle_secret_type=self.store_type,
#             encrypted_value=value,
#         )
#         self.secrets[secret.key] = secret
#         return secret

#     def retrieve_secret(self, secret: MindCastleSecret) -> str:
#         return self.secrets.get(secret.key).encrypted_value

#     def update_secret(self, secret: MindCastleSecret, value: str) -> MindCastleSecret:
#         new_secret = self.create_secret(value)
#         new_secret.key = secret.key
#         self.secrets[new_secret.key] = new_secret
#         return new_secret

#     def delete_secret(self, secret: MindCastleSecret) -> None:
#         del self.secrets[secret.key]
