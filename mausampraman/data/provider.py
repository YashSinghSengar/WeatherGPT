"""Weather provider boundary. App talks to provider, provider talks Open-Meteo.

Only canonical data crosses this boundary. Raw provider JSON never leaves
data/openmeteo_client.py. Method names follow the existing code.
"""
from data import openmeteo_client as oc
from data.openmeteo_client import (
    DataUnavailable,
    ProviderHTTPError,
    ProviderMalformed,
    ProviderTimeout,
    default_target_date,
    divergence_scenario_from_models,
    to_legacy_forecast,
)


class OpenMeteoProvider:
    """Current provider. Coordinates in, canonical weather out."""

    name = "openmeteo"

    def get_current(self, lat: float, lon: float) -> dict:
        """Current-weather view. Shares the single canonical fetch, no extra call."""
        return oc.get_canonical_weather(lat, lon)["current"]

    def get_forecast(self, lat: float, lon: float) -> dict:
        """Legacy forecast view. Same fetch, same numbers as always."""
        return oc.get_forecast(lat, lon)

    def get_canonical(self, lat: float, lon: float) -> dict:
        return oc.get_canonical_weather(lat, lon)

    def get_model_forecasts(self, lat: float, lon: float, date_str: str) -> dict:
        """Per-model aggregates for agreement. One call, shared by pipeline."""
        return oc.prevruns_per_model(lat, lon, date_str)

    def get_daily(self, lat: float, lon: float) -> list:
        return oc.get_daily(lat, lon)


provider = OpenMeteoProvider()


def get_canonical_weather(lat: float, lon: float) -> dict:
    return provider.get_canonical(lat, lon)


def get_forecast(lat: float, lon: float) -> dict:
    return provider.get_forecast(lat, lon)


def get_daily(lat: float, lon: float) -> list:
    return provider.get_daily(lat, lon)


def prevruns_per_model(lat: float, lon: float, date_str: str) -> dict:
    return provider.get_model_forecasts(lat, lon, date_str)

__all__ = ["OpenMeteoProvider", "provider", "DataUnavailable", "ProviderHTTPError",
           "ProviderMalformed", "ProviderTimeout", "default_target_date",
           "divergence_scenario_from_models", "get_canonical_weather", "get_daily",
           "get_forecast", "prevruns_per_model", "to_legacy_forecast"]
