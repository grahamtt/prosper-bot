from decimal import Decimal

from prosper_api.config import Config
from prosper_shared.omni_config import config_schema
from schema import Optional


@config_schema
def _schema():
    return {
        Optional(
            "bot", default={"dry-run": False, "verbose": False, "min-bid": Decimal(25)}
        ): {
            Optional("dry-run", default=False): bool,
            Optional("verbose", default=False): bool,
            Optional("min-bid", default=Decimal(25.00)): Decimal,
        }
    }


def build_config() -> Config:
    """Compiles all the config sources into a single config."""
    return Config.autoconfig(["prosper-api", "prosper-bot"], validate=True)
