"""Configuration for the pytest test suite."""

from os import environ

from funcy_bear import METADATA

environ[f"{METADATA.env_variable}"] = "test"
