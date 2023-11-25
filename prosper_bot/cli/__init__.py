import argparse
from decimal import Decimal
from os import getcwd
from os.path import join
from typing import List

from deepmerge import always_merger
from prosper_api.config import Config
from prosper_shared.omni_config.parse import (
    ArgParseSource,
    ConfigurationSource,
    EnvironmentVariableSource,
    TomlConfigurationSource,
)


def build_config():
    """Compiles all the config sources into a single config."""
    config_path = Config._DEFAULT_CONFIG_PATH

    conf_sources: List[ConfigurationSource] = [
        TomlConfigurationSource(config_path),
        TomlConfigurationSource(join(getcwd(), ".prosper-api.toml")),
        TomlConfigurationSource(join(getcwd(), ".pyproject.toml", "tools.prosper-api")),
        EnvironmentVariableSource("PROSPER_API", separator="__"),
        EnvironmentVariableSource("PROSPER_BOT", separator="__"),
        ArgParseSource(_arg_parser()),
    ]

    confs = [c.read() for c in conf_sources]

    conf = {"bot": {"min_bid": "25.00"}}

    for partial_conf in confs:
        always_merger.merge(conf, partial_conf)

    return conf


def _arg_parser():
    parser = argparse.ArgumentParser(
        prog="Prosper bot",
        description="A bot that can find and invest in loans according to the user's preferences",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        dest="bot__dry_run",
        help="Do everything but actually purchase the loans",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="bot__verbose",
        help="Print out verbose messages during trading loop",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--min-bid",
        dest="bot__min_bid",
        help="Minimum bid amount. Must be greater than or equal to 25",
        type=Decimal,
        default=Decimal("25"),
    )

    cred_group = parser.add_argument_group(
        "credentials",
    )
    cred_group.add_argument(
        "--client-id",
        dest="credentials__client_id",
        help="Prosper API client id to use with the requests",
    )
    cred_group.add_argument(
        "--client-secret",
        dest="credentials__client_secret",
        help="The secret corresponding to the client id; not recommended for use.",
    )
    cred_group.add_argument(
        "--username", dest="credentials__username", help="Prosper username"
    )
    cred_group.add_argument(
        "--password",
        dest="credentials__password",
        help="Prosper password; not recommended for use.",
    )

    auth_group = parser.add_argument_group("auth")
    auth_group.add_argument(
        "--token-cache",
        dest="auth__token_cache",
        help=f"Location to cache the authentication token and refresh token. Defaults to '{Config._DEFAULT_TOKEN_CACHE_PATH}'.",
    )

    client_group = parser.add_argument_group("client")
    client_group.add_argument(
        "--return-floats",
        dest="client__return_floats",
        help="Whether the API should return floating point primitives instead of decimals for currency values. Not recommended due to rounding issues.",
        action="store_true",
    )
    client_group.add_argument(
        "--return-strings-not-dates",
        dest="client__return_strings_not_dates",
        help="Whether the API should return strings for date fields instead of parsing them into 'datetime' objects.",
        action="store_true",
    )
    client_group.add_argument(
        "--return-strings-not-enums",
        dest="client__return_strings_not_enums",
        help="Whether the API should return strings for categorical fields instead of parsing them into the corresponding enum values.",
        action="store_true",
    )

    return parser
