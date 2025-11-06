# import os

# import boto3
# import botocore

# from mind_castle.secret_store_base import SecretStoreBase
# from mind_castle.exceptions import (
#     RetrieveSecretException,
#     CreateSecretException,
#     DeleteSecretException,
#     UpdateSecretException,
# )


# class AWSSecretsManagerSecretStore(SecretStoreBase):
#     """
#     Uses AWS Secrets Manager to store secrets.
#     """

#     store_type = "awssecretsmanager"
#     required_config = [
#         [
#             "MIND_CASTLE_AWS_REGION",
#             "MIND_CASTLE_AWS_ACCESS_KEY_ID",
#             "MIND_CASTLE_AWS_SECRET_ACCESS_KEY",
#         ],
#         ["MIND_CASTLE_AWS_REGION", "MIND_CASTLE_AWS_USE_ENV_AUTH"],
#     ]
#     optional_config = []

#     def __init__(self):
#         if all([os.environ.get(req) for req in self.required_config[0]]):
#             # Configure with secret key
#             self.client = boto3.client(
#                 "secretsmanager",
#                 region_name=os.environ["MIND_CASTLE_AWS_REGION"],
#                 aws_access_key_id=os.environ["MIND_CASTLE_AWS_ACCESS_KEY_ID"],
#                 aws_secret_access_key=os.environ["MIND_CASTLE_AWS_SECRET_ACCESS_KEY"],
#             )
#         else:
#             # Assume the environment is configured with the correct credentials
#             self.client = boto3.client(
#                 "secretsmanager", region_name=os.environ["MIND_CASTLE_AWS_REGION"]
#             )

#     def retrieve_secret(self, secret_details: dict) -> str:
#         key = secret_details.get("key")
#         try:
#             response = self.client.get_secret_value(SecretId=secret_details.get("key"))
#         except botocore.exceptions.ClientError as e:
#             raise RetrieveSecretException(e, key)

#         return response.get("SecretString")

#     def create_secret(self, key: str, value: str) -> dict:
#         # Response is always a success. This throws an exception if it fails
#         request_token = self.get_secret_key()
#         try:
#             response = self.client.create_secret(
#                 Name=key,
#                 ClientRequestToken=request_token,
#                 SecretString=value,
#                 # Other details we could add:
#                 # Description='string',
#                 # KmsKeyId='string',
#                 # SecretBinary=b'bytes',
#                 # Tags=[
#                 #     {
#                 #         'Key': 'string',
#                 #         'Value': 'string'
#                 #     },
#                 # ],
#                 # AddReplicaRegions=[
#                 #     {
#                 #         'Region': 'string',
#                 #         'KmsKeyId': 'string'
#                 #     },
#                 # ],
#                 # ForceOverwriteReplicaSecret=True|False
#             )
#         except botocore.exceptions.ClientError as e:
#             raise CreateSecretException(e)

#         # ARN is not needed but returned just in case. we could also add tags etc to this response
#         return {
#             "mind_castle_secret_type": self.store_type,
#             "request_token": request_token,
#             "key": key,
#             "arn": response.get("ARN"),
#         }

#     def update_secret(self, secret_details: dict, value: str) -> dict:
#         # Response is always a success. This throws an exception if it fails
#         key = secret_details.get("key")
#         request_token = self.get_secret_key()
#         try:
#             response = self.client.put_secret_value(
#                 SecretId=key,
#                 ClientRequestToken=request_token,
#                 SecretString=value,
#             )
#         except botocore.exceptions.ClientError as e:
#             raise UpdateSecretException(e)

#         # ARN is not needed but returned just in case. we could also add tags etc to this response
#         return {
#             "mind_castle_secret_type": self.store_type,
#             "request_token": request_token,
#             "key": key,
#             "arn": response.get("ARN"),
#         }

#     def delete_secret(self, secret_details: dict) -> None:
#         key = secret_details["key"]
#         # Response is always a success. This throws an exception if it fails
#         try:
#             self.client.delete_secret(SecretId=key)
#         except botocore.exceptions.ClientError as e:
#             raise DeleteSecretException(e, key)
