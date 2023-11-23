import argparse
import os
from os import getcwd
from os.path import join
from typing import Dict, List, Union

from deepmerge import always_merger
from merge_conf import ConfigurationSource
from merge_conf.toml import TomlConfigurationSource
from prosper_api.config import Config


def build_config():
    """Compiles all the config sources into a single config."""
    config_path = Config._DEFAULT_CONFIG_PATH

    conf_sources: List[ConfigurationSource] = [
        TomlConfigurationSource(config_path),
        TomlConfigurationSource(join(getcwd(), ".prosper-api.toml")),
        _MyEnvironmentVariableSource("PROSPER_API", separator="__"),
        _MyEnvironmentVariableSource("PROSPER_BOT", separator="__"),
        _MyArgParseSource(_arg_parser()),
    ]

    confs = [c.read() for c in conf_sources]

    conf = {}

    for partial_conf in confs:
        always_merger.merge(conf, partial_conf)

    return conf


class _MyArgParseSource(ConfigurationSource):
    def __init__(self, argument_parser: argparse.ArgumentParser):
        self._argument_parser = argument_parser

    def read(self) -> dict:
        raw_namespace = self._argument_parser.parse_args()
        nested_config = {}

        for key, val in raw_namespace.__dict__.items():
            if val is None or any(
                a
                for a in self._argument_parser._actions
                if key == a.dest and val == a.default
            ):
                continue
            key_components = key.split("__")
            config_namespace = nested_config
            for key_component in key_components[:-1]:
                if key_component not in config_namespace:
                    config_namespace[key_component] = {}
                config_namespace = config_namespace[key_component]
            config_namespace[key_components[-1]] = str(val)

        return nested_config


class _MyEnvironmentVariableSource(ConfigurationSource):
    """A configuration source for environment variables."""

    def __init__(
        self, prefix: str, separator: str = "_", list_separator: str = ","
    ) -> None:
        """Creates a new instance of the EnvironmentVariableSource.

        Args:
            prefix (str): The unique prefix for the environment variables.
            separator (str, optional): The value separator. Defaults to "_".
            list_separator (str, optional): If a value can be interpreted as a
                list, this will be used as separator.. Defaults to ",".
        """
        self.__prefix = prefix or ""
        self.__separator = separator
        self.__list_item_separator = list_separator
        super().__init__()

    def read(self) -> dict:
        """Reads the environment variables and produces a nested key-value list.

        Returns:
            dict: The mapped environment variables.
        """
        result = dict()
        value_map: Dict[str, str] = _MyEnvironmentVariableSource.__get_value_map()
        mapped_variables: List[str] = [
            key for (key, _) in value_map.items() if key.startswith(self.__prefix)
        ]
        for key in mapped_variables:
            value = value_map[key]
            sanitized: List[str] = self.__sanitize_key(key)
            items: dict = result
            for key_part in sanitized[:-1]:
                if key_part not in items.keys():
                    items[key_part.lower()] = dict()
                items = items[key_part.lower()]

            last_key: str = sanitized[-1]
            items[last_key.lower()] = self.__sanitize_value(value)

        return result

    @staticmethod
    def __get_value_map() -> Dict[str, str]:
        """Gets a list of key-value-pairs representing the environment variables.

        Returns:
            Dict[str, str]: The key-value map.
        """
        return os.environ

    def __sanitize_key(self, key: str) -> List[str]:
        """Splits a key according to the specified separators.

        Args:
            key (str): The key to split into lists.

        Returns:
            List[str]: The list of split keys.
        """
        if key is not None:
            working_ptr: str = key.lstrip(self.__prefix)
            return working_ptr.split(self.__separator)

        return [key]

    def __sanitize_value(self, value: str) -> Union[str, List[str]]:
        """Splits a value into a list, if applicable.

        Args:
            value (str): The value to parse.

        Returns:
            Union[str, List[str]]: The value parsed.
        """
        if value is not None:
            if self.__list_item_separator in value:
                return value.split(self.__list_item_separator)

            return value

        return ""


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
