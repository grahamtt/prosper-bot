from prosper_shared.omni_config import Config, ConfigKey, input_schema

DRY_RUN_CONFIG = "prosper-bot.cli.dry-run"
VERBOSE_CONFIG = "prosper-bot.cli.verbose"


@input_schema
def _schema():
    return {
        "prosper-bot": {
            "cli": {
                ConfigKey(
                    "verbose", "Prints additional debug messages.", default=False
                ): bool,
                ConfigKey(
                    "dry-run",
                    "Run the loop but don't actually place any orders.",
                    default=False,
                ): bool,
            }
        }
    }


def build_config() -> Config:
    """Compiles all the config sources into a single config."""
    return Config.autoconfig(validate=True)
