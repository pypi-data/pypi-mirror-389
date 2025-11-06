import pytest
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from mind_castle.stores.local_encryption import LocalEncryptionSecretStore
from mind_castle.secret_store_base import MindCastleSecret


@pytest.fixture(scope="module")
def aesgcm():
    key = base64.urlsafe_b64encode(os.urandom(16)).decode()
    os.environ["MIND_CASTLE_LOCAL_ENCRYPTION_SECRET"] = key
    return AESGCM(base64.urlsafe_b64decode(key))


def test_create_secret(aesgcm):
    secret_store = LocalEncryptionSecretStore()

    response = secret_store.create_secret("some_secret_value")

    blob = base64.urlsafe_b64decode(response.encrypted_value)
    nonce, ct = blob[:12], blob[12:]
    decrypted_value = aesgcm.decrypt(nonce, ct, None).decode()
    assert decrypted_value == "some_secret_value"
    assert response.mind_castle_secret_type == secret_store.store_type


def test_retrieve_secret(aesgcm):
    secret_store = LocalEncryptionSecretStore()
    secret = secret_store.create_secret("retrievable_secret")
    assert secret_store.retrieve_secret(secret) == "retrievable_secret"


def test_delete_secret(aesgcm):
    secret_store = LocalEncryptionSecretStore()
    secret_store.delete_secret(
        MindCastleSecret(
            mind_castle_secret_type=secret_store.store_type,
            encrypted_value="some_value",
        )
    )
    # Just shouldn't throw an error


def test_update_secret(aesgcm):
    secret_store = LocalEncryptionSecretStore()
    secret = secret_store.create_secret("updatable_secret")

    updated_secret = secret_store.update_secret(secret, "some_updated_value")

    blob = base64.urlsafe_b64decode(updated_secret.encrypted_value)
    nonce, ct = blob[:12], blob[12:]
    decrypted_value = aesgcm.decrypt(nonce, ct, None).decode()
    assert decrypted_value == "some_updated_value"
    assert updated_secret.mind_castle_secret_type == secret_store.store_type
