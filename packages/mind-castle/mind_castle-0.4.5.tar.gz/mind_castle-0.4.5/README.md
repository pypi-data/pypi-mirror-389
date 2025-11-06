# Mind Castle - Build a wall around your secrets

A universal store for your secret data. Don't delay securing you or your customer's data by deliberating over cloud secret stores. Mind Castle makes it easy to get started, and easy to switch between cloud secret stores.

Mind Castle currently supports:
- AWS KMS
- Local Encryption
- None (passthrough - Mind Castle doesn't modify your data)

## Architecture

Mind Castle comes in three parts:
- A unified interface for several secret stores.
- An SQLAlchemy column type that transparently stores and retrieves secrets for you.
- A migration tool to convert your existing DB column data into secrets.

Some other notes:
- Mind Castle is configured and secret stores are initialised at import time. That means env-vars used for configuration need to be defined when Mind Castle is imported.
- Mind Castle makes no attempt to manage secrets in memory. [Memory management](https://stackoverflow.com/questions/728164/securely-erasing-password-in-memory-python) in [Python](https://discuss.python.org/t/how-to-hide-or-remove-sensitive-data-from-getting-exposed-in-memory-dump/44526) is [futile](https://stackoverflow.com/questions/41509771/python-remove-password-from-memory), and if you need that level of control it's best to use another language.


## Install

`pip install mind-castle`


## Configure

You can configure Mind Castle by setting environment variables for your chosen secret store. To see what configuration options are required for each store:

```bash
$ python -m mind_castle
╭───────────────────────────────────────── MIND CASTLE ─────────────────────────────────────────╮
│                                                                                               │
│                                         Secret Stores                                         │
│ ┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃ Store Type        ┃ Required env var                  ┃ Optional env var                  ┃ │
│ ┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩ │
│ │ memory            │                                   │                                   │ │
│ │                   │                                   │                                   │ │
│ │ plaintext         │                                   │                                   │ │
│ │                   │                                   │                                   │ │
│ │ awssecretsmanager │ MIND_CASTLE_AWS_REGION            │ MIND_CASTLE_AWS_SECRET_KEY_PREFIX │ │
│ │                   │ MIND_CASTLE_AWS_ACCESS_KEY_ID     │                                   │ │
│ │                   │ MIND_CASTLE_AWS_SECRET_ACCESS_KEY │                                   │ │
│ │                   │ --- OR ---                        │                                   │ │
│ │                   │ MIND_CASTLE_AWS_REGION            │ MIND_CASTLE_AWS_SECRET_KEY_PREFIX │ │
│ │                   │ MIND_CASTLE_AWS_USE_ENV_AUTH      │                                   │ │
│ │                   │                                   │                                   │ │
│ │ hashicorpvault    │ MIND_CASTLE_VAULT_HOST            │                                   │ │
│ │                   │ MIND_CASTLE_VAULT_TOKEN           │                                   │ │
│ │                   │                                   │                                   │ │
│ │ json              │                                   │                                   │ │
│ │                   │                                   │                                   │ │
│ └───────────────────┴───────────────────────────────────┴───────────────────────────────────┘ │
╰───────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Use

### Migrating Existing Data
A migration tool is provided to move your existing data into a secret store. The tool assumes you have a database that can be connected to using SQLAlchemy and `create_engine(<db_uri>)`.

You will need to configure your selected secret store using environment variables as described above. You can see what other options the migration tool accepts with:

```bash
$ python migration_tool.py --help

 Usage: migration_tool.py [OPTIONS] DB_URI

╭─ Arguments ─────────────────────────────────────────────────────────────────────────╮
│ *    db_uri      TEXT  [default: None] [required]                                   │
╰─────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ───────────────────────────────────────────────────────────────────────────╮
│ --target-table                        TEXT  [default: None]                         │
│ --target-column                       TEXT  [default: None]                         │
│ --dry-run           --no-dry-run            [default: dry-run]                      │
│ --demigrate         --no-demigrate          [default: no-demigrate]                 │
│ --to-secret-type                      TEXT  [default: json]                         │
│ --help                                      Show this message and exit.             │
╰─────────────────────────────────────────────────────────────────────────────────────╯
```

The easiest thing to do is specify `--to-secret-type` and let the tool guide you through the rest. e.g.:

```bash
$ MIND_CASTLE_VAULT_HOST="http://127.0.0.1:8200" MIND_CASTLE_VAULT_TOKEN="<your_token>" python migration_tool.py "postgresql://<user>:<pass>@<host>:5432/<database>" --to-secret-type hashicorpvault
```

The tool will list tables and columns in the selected DB for you, and ask you to select each. Once a dry run is complete and **you also have a backup of your database**, you can add `--no-dry-run` to migrate the data for real.


### SQLAlchemy Model
Once any existing data is migrated, you can update your SQLAlchemy model to include a `SecretData` column:

```python
from mind_castle.sqlalchemy_type import SecretData

class MyDBModel(Base):
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now)
    secret_data = Column(SecretData("hashicorpvault"))
```

Your secrets will then be safely stored in Vault (or AWS, or anywhere else you like)! The storage and retrieval of secrets will be completely transparent to your application.


## TODO

- Make migration script work for non-json columns
- Support deleting secrets when row is deleted
- Implement prefixes/folders for secrets
- Explain how secrets are stored
- Enforce tests on PR / branch protections