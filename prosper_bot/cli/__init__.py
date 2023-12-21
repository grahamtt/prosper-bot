from prosper_shared.omni_config import Config, ConfigKey, input_schema

DRY_RUN_CONFIG = "cli.dry-run"
VERBOSE_CONFIG = "cli.verbose"
SIMULATE_CONFIG = "cli.simulate"


@input_schema
def _schema():
    return {
        "cli": {
            ConfigKey(
                "verbose", "Prints additional debug messages.", default=False
            ): bool,
            ConfigKey(
                "dry-run",
                "Run the loop but don't actually place any orders.",
                default=False,
            ): bool,
            ConfigKey(
                "simulate",
                "Run the loop as if the account had the minimum bid amount. Implies `dry-run`.",
                default=False,
            ): bool,
        }
    }


def build_config() -> Config:
    """Compiles all the config sources into a single config."""
    return Config.autoconfig(["prosper-api", "prosper-bot"], validate=True)
