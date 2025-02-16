from prosper_shared.omni_config import Config, ConfigKey, input_schema

DRY_RUN_CONFIG = "prosper-bot.cli.dry-run"
VERBOSE_CONFIG = "prosper-bot.cli.verbose"
SINGLE_RUN_CONFIG = "prosper-bot.cli.single-run"
APP_NAME = "prosper-bot"


@input_schema
def _schema():
    return {
        APP_NAME: {
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
                    "single-run",
                    "Runs the loop only once, or until cash is exhausted",
                    default=False,
                ): bool,
            }
        }
    }


def build_config() -> Config:
    """Compiles all the config sources into a single config."""
    return Config.autoconfig(APP_NAME, validate=True)
