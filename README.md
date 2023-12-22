# prosper-bot

Bot to automatically invest in prosper.com

[![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/grahamtt/prosper-bot/build-and-release.yml?logo=github)](https://github.com/grahamtt/prosper-bot)
[![PyPI - Version](https://img.shields.io/pypi/v/prosper-bot?label=prosper-bot)](https://pypi.org/project/prosper-bot/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/prosper-bot)
![PyPI - License](https://img.shields.io/pypi/l/prosper-bot)
[![Code Climate coverage](https://img.shields.io/codeclimate/coverage/grahamtt/prosper-bot?logo=codeclimate)](https://codeclimate.com/github/grahamtt/prosper-bot)
[![Code Climate maintainability](https://img.shields.io/codeclimate/maintainability-percentage/grahamtt/prosper-bot?logo=codeclimate)](https://codeclimate.com/github/grahamtt/prosper-bot)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/8107/badge)](https://www.bestpractices.dev/projects/8107)
![GitHub commit activity (branch)](https://img.shields.io/github/commit-activity/m/grahamtt/prosper-bot?logo=github)
![GitHub issues](https://img.shields.io/github/issues-raw/grahamtt/prosper-bot?logo=github)

## Installation

Use [`pipx`](https://pypa.github.io/pipx/) to install in a self-contained virtual environment.

```commandline
pipx install prosper-bot
```

## Setup

Follow the [setup instructions](https://github.com/grahamtt/prosper-api#setup) for Prosper API

## Running

### Dry run

```commandline
prosper-bot --dry-run
```

### For realsies

```commandline
prosper-bot
```

## Options

Prosper bot exposes all the config options from `prosper-api`, plus the options in the `bot` and `cli` sections below.

```
usage: prosper-bot [-h] [--use-decimals] [--parse-dates] [--parse-enums] [--client-id CLIENT-ID]
                   [--client-secret CLIENT-SECRET] [--username USERNAME] [--password PASSWORD]
                   [--token-cache TOKEN-CACHE] [--min-bid MIN-BID]
                   [--strategy {AGGRESSIVE,CONSERVATIVE}] [--verbose] [--dry-run] [--simulate]

options:
  -h, --help            show this help message and exit

prosper_shared:

prosper_shared.serde:

  --use-decimals        Floating point values should be parsed as decimals instead of floats.;
                        Type: bool; Default: True
  --parse-dates         Date values represented as strings should be parsed into `date` and
                        `datetime` objects. Supports ISO-8601-compliant date strings.; Type: bool;
                        Default: True
  --parse-enums         Enum values represented as strings should be parsed into their respective
                        types.; Type: bool; Default: True

prosper_api:

prosper_api.credentials:

  --client-id CLIENT-ID
                        The client-id from Prosper.; Type: str matching /^[a-f0-9]{32}$/
  --client-secret CLIENT-SECRET
                        The client-secret from Prosper; can be configured using the keyring
                        library.; Type: str matching /^[a-f0-9]{32}$/
  --username USERNAME   Your Prosper username; Type: str
  --password PASSWORD   Your Prosper password; can be configured using the keyring library.; Type:
                        str

prosper_api.auth:

  --token-cache TOKEN-CACHE
                        The filesystem location where the auth token will be cached.; Type: str;
                        Default: /home/graham/.cache/prosper-api/token-cache

prosper_bot:

prosper_bot.bot:

  --min-bid MIN-BID     Minimum amount of a loan to purchase.; Type: Decimal; Default: 25.00
  --strategy {AGGRESSIVE,CONSERVATIVE}
                        Strategy for balancing your portfolio.; Type: str; Default: AGGRESSIVE

prosper_bot:

prosper_bot.cli:

  --verbose             Prints additional debug messages.; Type: bool; Default: False
  --dry-run             Run the loop but don't actually place any orders.; Type: bool; Default:
                        False
  --simulate            Run the loop as if the account had the minimum bid amount. Implies `dry-
                        run`.; Type: bool; Default: False
```
