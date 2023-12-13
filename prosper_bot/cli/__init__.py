from decimal import Decimal

from prosper_shared.omni_config import Config, input_schema
from schema import Optional

DRY_RUN_CONFIG = "cli.dry-run"
VERBOSE_CONFIG = "cli.verbose"


@input_schema
def _schema():
    return {
        Optional(
            "cli", default={"dry-run": False, "verbose": False, "min-bid": Decimal(25)}
        ): {
            Optional("dry-run", default=False): bool,
            Optional("verbose", default=False): bool,
        }
    }


def build_config() -> Config:
    """Compiles all the config sources into a single config."""
    return Config.autoconfig(["prosper-api", "prosper-bot"], validate=True)
