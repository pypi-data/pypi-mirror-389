from datetime import datetime

import pandas as pd
from easyprov import csv_dump, csv_header

from .api import WeatherServerApi
from .rac5 import closest_ref, fetch_hourly


class Rac5HourlyServer(WeatherServerApi):

    def __init__(self):
        super().__init__()
        self.storage = self.storage_root() / "rac5_hourly"

    def pth_storage(self, latitude, longitude, year):
        """Normalized name associated to given coordinates

        Args:
            latitude (float): [deg] latitude of place
            longitude (float): [deg] longitude of place
            year (int): year of time series

        Returns:
            (str)
        """
        return self.storage / f"{year:d}/rac5_{int((latitude + 90) * 100):05d}_{int((longitude + 180) * 100):05d}.csv"

    def exists(self, latitude, longitude, year):
        """Check whether file has already been fetched from server

        Args:
            latitude (float): [deg] latitude of place
            longitude (float): [deg] longitude of place
            year (int): [-] year to fetch from YYYY-01-01T00:00 till YYYY-12-31T24:00

        Returns:
            (bool)
        """
        return self.pth_storage(latitude, longitude, year).exists()

    def header(self):
        """Header of data stored

        Returns:
            (dict): [unit] description per columns
        """
        pth_dir = list(self.storage.glob("*/"))[0]
        pth = list(pth_dir.glob("*.csv"))[0]
        return csv_header(pth)

    def get(self, latitude, longitude, year, closest=True, fetch=False):
        """Get time series for given location from local storage.

        Raises: if not fetch, KeyError if either pos or year has not been fetch
                previously on server

        Args:
            latitude (float): [deg] latitude of place
            longitude (float): [deg] longitude of place
            year (int): [-] year to fetch from YYYY-01-01T00:00 till YYYY-12-31T24:00
            closest (bool): Whether to interpolate from nearby locations or fetch
                            only nearest point in model
            fetch (bool): whether to fetch missing entry from remote server or raise error

        Returns:
            (pd.DataFrame): name of columns varies
        """
        assert closest

        ref_lat, ref_long = closest_ref(latitude, longitude)
        pth = self.pth_storage(ref_lat, ref_long, year)
        if not pth.exists():
            if fetch:
                self.fetch(ref_lat, ref_long, year)
            else:
                raise KeyError("File not available in local storage, need to fetch")

        df = pd.read_csv(pth, sep=";", comment="#", parse_dates=["date"], index_col=["date"])

        return df

    def fetch(self, latitude, longitude, year):
        """Fetch time series for given location on remote server

        Notes: does nothing if data already in storage

        Args:
            latitude (float): [deg] latitude of place
            longitude (float): [deg] longitude of place
            year (int): [-] year to fetch from YYYY-01-01T00:00 till YYYY-12-31T23:00 included

        Returns:
            None
        """
        ref_lat, ref_long = closest_ref(latitude, longitude)
        pth = self.pth_storage(ref_lat, ref_long, year)
        if pth.exists():
            print("already")
            return

        # fetch
        df, header = fetch_hourly(ref_lat, ref_long, datetime(year, 1, 1), datetime(year, 12, 31))

        # write
        pth.parent.mkdir(exist_ok=True, parents=True)
        csv_dump(df, header, pth, __file__, float_format="%.2f")
