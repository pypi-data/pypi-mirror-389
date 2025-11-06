import uuid
import os
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class MindCastleSecret(BaseModel):
    key: uuid.UUID = Field(default_factory=uuid.uuid1)
    mind_castle_secret_type: str
    encrypted_value: str
    metadata: dict = Field(default_factory=dict)


class SecretStoreBase(ABC):
    """This is an abstract class that defines the interface for a secret store."""

    store_type = "base"
    required_config = [[]]
    optional_config = []
    key_prefix = os.environ.get("MIND_CASTLE_SECRET_KEY_PREFIX", "")

    @abstractmethod
    def create_secret(self, value: str) -> MindCastleSecret:
        raise NotImplementedError()

    @abstractmethod
    def retrieve_secret(self, secret: MindCastleSecret) -> str:
        raise NotImplementedError()

    @abstractmethod
    def update_secret(self, secret: MindCastleSecret, value: str) -> MindCastleSecret:
        raise NotImplementedError()

    @abstractmethod
    def delete_secret(self, secret: MindCastleSecret) -> None:
        raise NotImplementedError()
