import os
import boto3
import botocore
import logging
import base64

from mind_castle.secret_store_base import SecretStoreBase, MindCastleSecret
from mind_castle.exceptions import (
    RetrieveSecretException,
    CreateSecretException,
)

logger = logging.getLogger(__name__)


class AWSKMSSecretStore(SecretStoreBase):
    """
    Uses AWS KMS to encrypt secrets.
    """

    store_type = "awskms"
    required_config = [
        [
            "MIND_CASTLE_AWS_REGION",
            "MIND_CASTLE_AWS_KMS_KEY_ID",
            "MIND_CASTLE_AWS_SECRET_ACCESS_KEY",
            "MIND_CASTLE_AWS_KMS_KEY_ARN",
        ],
        [
            "MIND_CASTLE_AWS_REGION",
            "MIND_CASTLE_AWS_USE_ENV_AUTH",
            "MIND_CASTLE_AWS_KMS_KEY_ARN",
        ],
    ]
    optional_config = []

    KMS_ENCRYPTION_ALGORITHM = "RSAES_OAEP_SHA_256"

    def __init__(self):
        if all([os.environ.get(req) for req in self.required_config[0]]):
            # Configure with secret key
            self.client = boto3.client(
                "kms",
                region_name=os.environ["MIND_CASTLE_AWS_REGION"],
                aws_access_key_id=os.environ["MIND_CASTLE_AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["MIND_CASTLE_AWS_SECRET_ACCESS_KEY"],
            )
        else:
            # Assume the environment is configured with the correct credentials
            self.client = boto3.client(
                "kms", region_name=os.environ["MIND_CASTLE_AWS_REGION"]
            )
        self.kms_key_arn = os.environ["MIND_CASTLE_AWS_KMS_KEY_ARN"]

    def retrieve_secret(self, secret: MindCastleSecret) -> str:
        encrypted_value = secret.encrypted_value
        try:
            response = self.client.decrypt(
                KeyId=self.kms_key_arn,
                EncryptionAlgorithm=self.KMS_ENCRYPTION_ALGORITHM,
                CiphertextBlob=base64.b64decode(encrypted_value),
            )
        except botocore.exceptions.ClientError as e:
            logger.exception(f"Error retrieving secret {secret.key}:")
            raise RetrieveSecretException(e, encrypted_value)

        return response.get("Plaintext").decode("utf-8")

    def create_secret(self, value: str) -> MindCastleSecret:
        try:
            # Response is always a success. This throws an exception if it fails
            response = self.client.encrypt(
                KeyId=self.kms_key_arn,
                EncryptionAlgorithm=self.KMS_ENCRYPTION_ALGORITHM,
                Plaintext=value.encode("utf-8"),
            )
        except botocore.exceptions.ClientError as e:
            raise CreateSecretException(e)

        # ARN is not needed but returned just in case. we could also add tags etc to this response
        return MindCastleSecret(
            mind_castle_secret_type=self.store_type,
            encrypted_value=base64.b64encode(response.get("CiphertextBlob")).decode(
                "utf-8"
            ),
        )

    def update_secret(self, secret: MindCastleSecret, value: str) -> MindCastleSecret:
        new_secret = self.create_secret(value)
        new_secret.key = secret.key
        return new_secret

    def delete_secret(self, secret: MindCastleSecret) -> None:
        pass
