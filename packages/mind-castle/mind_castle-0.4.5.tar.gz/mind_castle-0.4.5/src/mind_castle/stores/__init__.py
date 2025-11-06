import glob
import logging
import os
import json
from typing import Any
from os.path import basename, dirname, isfile, join

from mind_castle.secret_store_base import SecretStoreBase, MindCastleSecret
from mind_castle.exceptions import RetrieveSecretException

import importlib

# Dynamically import all .py files in the current package except __init__.py
modules = glob.glob(join(dirname(__file__), "*.py"))
for f in modules:
    if isfile(f) and not f.endswith("__init__.py"):
        module_name = basename(f)[:-3]
        importlib.import_module(f".{module_name}", package=__name__)


logger = logging.getLogger(__name__)

# Get all env vars with our prefix
env_vars = {k: v for k, v in os.environ.items() if k.startswith("MIND_CASTLE_")}

stores = {}

# Populate 'stores' dict with instantiated stores
for subclass in SecretStoreBase.__subclasses__():
    configured = False
    for config_set in subclass.required_config:
        if all(e in env_vars.keys() for e in config_set):
            stores[subclass.store_type] = subclass()
            secret_store = subclass()
            logger.debug(f"Configured secret store '{subclass.store_type}'")
            configured = True

        elif not configured and any(e in env_vars.keys() for e in config_set):
            # Log a warning if some but not all required config is present
            logger.warning(
                f"Missing required config for store '{subclass.store_type}'. Requires: {config_set}"
            )


def create_secret(value: Any, secret_type: str) -> MindCastleSecret:
    value = json.dumps(value)
    secret_store = stores.get(secret_type)
    if secret_store is None:
        raise ValueError(
            f"Trying to put secret to unknown/unconfigured store '{secret_type}'"
        )

    return secret_store.create_secret(value)


def retrieve_secret(secret: MindCastleSecret) -> Any:
    secret_type = secret.mind_castle_secret_type
    if secret_type is None:
        raise ValueError("No mind_castle_secret_type provided in secret")

    secret_store = stores.get(secret_type)
    if secret_store is None:
        raise ValueError(
            f"Trying to retrieve secret from unknown/unconfigured store '{secret_type}'"
        )
    response = secret_store.retrieve_secret(secret)
    if response is None:
        raise RetrieveSecretException(
            None,
            f"Secret of type {secret_type} with key {secret.key} not found.",
        )
    return json.loads(response)


def update_secret(secret: MindCastleSecret, value: str) -> MindCastleSecret:
    secret_type = secret.mind_castle_secret_type
    if secret_type is None:
        raise ValueError("No mind_castle_secret_type provided in data")

    secret_store = stores.get(secret_type)
    if secret_store is None:
        raise ValueError(
            f"Trying to put secret to unknown/unconfigured store '{secret_type}'"
        )

    return secret_store.update_secret(secret, value)


def delete_secret(secret: MindCastleSecret) -> None:
    secret_type = secret.mind_castle_secret_type
    if secret_type is None:
        raise ValueError("No mind_castle_secret_type provided in data")

    secret_store = stores.get(secret_type)
    if secret_store is None:
        raise ValueError(
            f"Trying to retrieve secret from unknown/unconfigured store '{secret_type}'"
        )
    return secret_store.delete_secret(secret)
