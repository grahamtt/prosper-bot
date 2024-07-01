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

```bash
pipx install prosper-bot
```

## Setup

Follow the [setup instructions](https://github.com/grahamtt/prosper-api#setup) for Prosper API

## Running

### Dry run

```bash
prosper-bot --dry-run
```

### For realsies

```bash
prosper-bot
```

## Options

Prosper bot exposes all the config options from `prosper-api`, plus the options in the `bot` and `cli` sections below.

```yaml
prosper-api.auth.token-cache:
  default: /Users/graham/Library/Caches/prosper-api/token-cache
  description: The filesystem location where the auth token will be cached.
  optional: false
  type: str
prosper-api.credentials.client-id:
  constraint: ^[a-f0-9]{32}$
  description: The client-id from Prosper.
  optional: false
  type: str
prosper-api.credentials.client-secret:
  constraint: ^[a-f0-9]{32}$
  description: The client-secret from Prosper; can be stored and accessed securely using the keyring
    library.
  optional: true
  type: str
prosper-api.credentials.password:
  description: Your Prosper password; can be stored and accessed securely using the keyring library.
  optional: true
  type: str
prosper-api.credentials.username:
  description: Your Prosper username
  optional: false
  type: str
prosper-bot.cli.dry-run:
  description: Run the loop but don't actually place any orders.
  optional: false
  type: bool
prosper-bot.cli.verbose:
  description: Prints additional debug messages.
  optional: false
  type: bool
```

All configs can be provided as command-line options as well:

```
usage: prosper-bot [-h] [-c CLIENT-ID] [--client-secret CLIENT-SECRET] [-u USERNAME]
                   [-p PASSWORD] [-t TOKEN-CACHE] [-m MIN-BID]
                   [-s {AGGRESSIVE,CONSERVATIVE,OVERALL_HIGHEST_RATE}]
                   [--target-loan-count TARGET-LOAN-COUNT] [-v] [-d]

options:
  -h, --help            show this help message and exit

prosper-api.credentials:
  -c CLIENT-ID, --client-id CLIENT-ID
                        The client-id from Prosper; Type: str matching /^[a-f0-9]{32}$/
  --client-secret CLIENT-SECRET
                        The client-secret from Prosper; can be stored and accessed securely
                        using the keyring library; Type: str matching /^[a-f0-9]{32}$/
  -u USERNAME, --username USERNAME
                        Your Prosper username; Type: str
  -p PASSWORD, --password PASSWORD
                        Your Prosper password; can be stored and accessed securely using the
                        keyring library; Type: str

prosper-api.auth:
  -t TOKEN-CACHE, --token-cache TOKEN-CACHE
                        The filesystem location where the auth token will be cached; Type:
                        str; Default: /Users/graham/Library/Caches/prosper-api/token-cache

prosper-bot.bot:
  -m MIN-BID, --min-bid MIN-BID
                        Minimum amount of a loan to purchase; Type: Decimal; Default: 25.00
  -s {AGGRESSIVE,CONSERVATIVE,OVERALL_HIGHEST_RATE}, --strategy {AGGRESSIVE,CONSERVATIVE,OVERALL_HIGHEST_RATE}
                        Strategy for balancing your portfolio; Type: str; Default:
                        AGGRESSIVE
  --target-loan-count TARGET-LOAN-COUNT
                        Calculate min bid based on (total account value / target loan
                        count). Overrides min-bid if present; Type: int

prosper-bot.cli:
  -v, --verbose         Prints additional debug messages; Type: bool
  -d, --dry-run         Run the loop but don't actually place any orders; Type: bool
```

## Feedback

This project uses [GitHub issues](https://github.com/grahamtt/prosper-bot/issues) for feature requests and bug reports.

## Contributing

This project uses [Poetry](https://python-poetry.org/docs/) to manage dependencies and building. Follow the instructions
to install it. Then use `poetry install --all-extras` to install the project dependencies. Then run `poetry run autohooks activate`
to set up the pre-commit hooks. Please ensure the hooks pass before submitting a pull request.
