import json
from datetime import datetime

import pandas as pd
import requests

# api
base_url = "https://archive-api.open-meteo.com/v1/archive"

cmap_daily = {
    "temperature_2m_max": "t_air_max",
    "temperature_2m_min": "t_air_min",
    "precipitation_sum": "rain",
    "shortwave_radiation_sum": "ghi",
    "et0_fao_evapotranspiration": "eto",

}

cmap_hourly = {
    "temperature_2m": "t_air",
    "relative_humidity_2m": "rh",
    "precipitation": "rain",
    "shortwave_radiation": "ghi",
    "wind_speed_10m": "ws",
    "et0_fao_evapotranspiration": "eto",
}


def closest_ref(latitude, longitude):
    """Closest point on rac5 grid

    Args:
        latitude (float): [deg] latitude
        longitude (float): [deg] longitude

    Returns:
        (float, float): [deg]
    """
    ref_lat = int((90 + latitude) * 4 + 0.5) / 4 - 90
    ref_long = int((180 + longitude) * 4 + 0.5) / 4 - 180

    return ref_lat, ref_long


def latitude_ref(latitude):
    """Latitude of reference points around latitude

    Args:
        latitude (float): [deg] latitude

    Returns:
        (float, float): [deg]
    """
    lat_min = int((90 + latitude) * 4) / 4 - 90
    lat_max = int(latitude * 4 + 1) / 4
    return lat_min, lat_max


def longitude_ref(longitude):
    """Longitude of reference points around longitude

    Args:
        longitude (float): [deg] longitude

    Returns:
        (float, float): [deg]
    """
    long_min = int((180 + longitude) * 4) / 4 - 180
    long_max = int(longitude * 4 + 1) / 4
    return long_min, long_max


def fetch_daily(latitude, longitude, date_beg, date_end):
    """Fetch time series for given location on remote server

    Args:
        latitude (float): [deg] latitude of place
        longitude (float): [deg] longitude of place
        date_beg (datetime): First date, included
        date_end (datetime): End date, included

    Returns:
        (pd.DataFrame, dict): date, header
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date_beg.date().isoformat(),
        "end_date": date_end.date().isoformat(),
        "wind_speed_unit": "ms",
        "daily": list(cmap_daily.keys())
    }

    # fetch
    response = requests.get(url=base_url, params=params, verify=True, timeout=30.00)

    cnt = response.content
    data = json.loads(cnt)
    if "daily" not in data:
        raise UserWarning(data)

    df = pd.DataFrame(data["daily"])
    df = df.rename(columns=cmap_daily | {'time': 'date'})
    df["date"] = pd.to_datetime(df["date"])

    # format header
    units = {name_norm: data["daily_units"][name] for name, name_norm in cmap_daily.items()}
    assert units["ghi"] == "MJ/m²"
    units["ghi"] = "MJ.m-2"
    assert units["rain"] == "mm"
    units["rain"] = "mm.h-1"
    assert units["eto"] == "mm"
    units["eto"] = "mm.h-1"

    header = {name: f"[{unit}]" for name, unit in units.items()}
    header["date"] = "[utc] see https://open-meteo.com/en/docs/historical-weather-api"
    header["latitude"] = f"[deg] {latitude:.6f}"
    header["longitude"] = f"[deg] {longitude:.6f}"

    return df.set_index("date"), header


def fetch_hourly(latitude, longitude, date_beg, date_end):
    """Fetch time series for given location on remote server

    Args:
        latitude (float): [deg] latitude of place
        longitude (float): [deg] longitude of place
        date_beg (datetime): First date, included
        date_end (datetime): End date, included

    Returns:
        (pd.DataFrame, dict): date, header
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": date_beg.date().isoformat(),
        "end_date": date_end.date().isoformat(),
        "wind_speed_unit": "ms",
        "hourly": list(cmap_hourly.keys())
    }

    # fetch
    response = requests.get(url=base_url, params=params, verify=True, timeout=30.00)

    cnt = response.content
    data = json.loads(cnt)
    if "hourly" not in data:
        raise UserWarning(data)

    df = pd.DataFrame(data["hourly"])
    df = df.rename(columns=cmap_hourly | {'time': 'date'})
    df["date"] = pd.to_datetime(df["date"])

    # format header
    units = {name_norm: data["hourly_units"][name] for name, name_norm in cmap_hourly.items()}
    assert units["ghi"] == "W/m²"
    units["ghi"] = "W.m-2"
    assert units["ws"] == "m/s"
    units["ws"] = "m.s-1"
    assert units["rain"] == "mm"
    units["rain"] = "mm.h-1"
    assert units["eto"] == "mm"
    units["eto"] = "mm.h-1"

    header = {name: f"[{unit}]" for name, unit in units.items()}
    header["date"] = "[utc] see https://open-meteo.com/en/docs/historical-weather-api"
    header["latitude"] = f"[deg] {latitude:.6f}"
    header["longitude"] = f"[deg] {longitude:.6f}"

    return df.set_index("date"), header
