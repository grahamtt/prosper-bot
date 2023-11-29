import argparse
from decimal import Decimal

from prosper_api import auth_token_manager
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
    return Config.autoconfig(
        ["prosper-api", "prosper-bot"], _arg_parser(), validate=True
    )


def _arg_parser():
    parser = argparse.ArgumentParser(
        prog="prosper-bot",
        description="A bot that can find and invest in loans according to the user's preferences",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        dest="bot__dry-run",
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
        dest="bot__min-bid",
        help="Minimum bid amount. Must be greater than or equal to 25",
        type=Decimal,
        default=Decimal("25"),
    )

    cred_group = parser.add_argument_group(
        "credentials",
    )
    cred_group.add_argument(
        "--client-id",
        dest="credentials__client-id",
        help="Prosper API client id to use with the requests",
    )
    cred_group.add_argument(
        "--client-secret",
        dest="credentials__client-secret",
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
        dest="auth__token-cache",
        help=f"Location to cache the authentication token and refresh token. Defaults to '{auth_token_manager._DEFAULT_TOKEN_CACHE_PATH}'.",
    )

    client_group = parser.add_argument_group("client")
    client_group.add_argument(
        "--return-floats",
        dest="client__return-floats",
        help="Whether the API should return floating point primitives instead of decimals for currency values. Not recommended due to rounding issues.",
        action="store_true",
    )
    client_group.add_argument(
        "--return-strings-not-dates",
        dest="client__return-strings-not-dates",
        help="Whether the API should return strings for date fields instead of parsing them into 'datetime' objects.",
        action="store_true",
    )
    client_group.add_argument(
        "--return-strings-not-enums",
        dest="client__return-strings-not-enums",
        help="Whether the API should return strings for categorical fields instead of parsing them into the corresponding enum values.",
        action="store_true",
    )

    return parser
