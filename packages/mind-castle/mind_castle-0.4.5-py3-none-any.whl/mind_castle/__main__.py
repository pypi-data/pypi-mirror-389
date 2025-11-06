from rich.table import Table
from rich import print
from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from mind_castle import stores  # noqa: F401
from mind_castle.secret_store_base import SecretStoreBase


header = Text("\n[bold underline]Mind Castle[/bold underline]\n", justify="center")

table = Table(title="Secret Stores")
table.add_column("Store Type", justify="left", style="cyan bold")
table.add_column("Required env var", justify="left", style="magenta")
table.add_column("Optional env var", justify="left", style="green")

for store in SecretStoreBase.__subclasses__():
    for config_set in range(len(store.required_config)):
        if config_set > 0:
            table.add_row("", "--- OR ---", "")
        table.add_row(
            store.store_type if config_set == 0 else "",
            "\n".join(store.required_config[config_set]),
            "\n".join(store.optional_config),
        )
    table.add_row("", "", "")

print(Panel.fit(Group(Text(), table), title="MIND CASTLE"))
