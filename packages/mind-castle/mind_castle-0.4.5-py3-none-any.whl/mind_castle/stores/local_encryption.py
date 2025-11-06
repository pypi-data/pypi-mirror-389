import os
import logging
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from mind_castle.secret_store_base import SecretStoreBase, MindCastleSecret

logger = logging.getLogger(__name__)


class LocalEncryptionSecretStore(SecretStoreBase):
    """
    Uses a local secret to encrypt and store cyphertext in the DB.
    """

    store_type = "localencryption"
    required_config = [
        [
            "MIND_CASTLE_LOCAL_ENCRYPTION_SECRET",
        ]
    ]
    optional_config = []

    def __init__(self):
        self.aesgcm = AESGCM(
            base64.urlsafe_b64decode(
                os.environ.get("MIND_CASTLE_LOCAL_ENCRYPTION_SECRET")
            )
        )

    def retrieve_secret(self, secret: MindCastleSecret) -> str:
        blob = base64.urlsafe_b64decode(secret.encrypted_value)
        nonce, ct = blob[:12], blob[12:]
        return self.aesgcm.decrypt(nonce, ct, None).decode()

    def create_secret(self, value: str) -> MindCastleSecret:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, value.encode(), None)
        return MindCastleSecret(
            mind_castle_secret_type=self.store_type,
            encrypted_value=base64.b64encode(nonce + ciphertext).decode(),
        )

    def update_secret(self, secret: MindCastleSecret, value: str) -> MindCastleSecret:
        new_secret = self.create_secret(value)
        new_secret.key = secret.key
        return new_secret

    def delete_secret(self, secret: MindCastleSecret) -> None:
        pass
