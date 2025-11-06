from pathlib import Path


class WeatherServerApi:
    """Base class for all models

    Each model must implement a derived class from this one

    The main objective is to encapsulate the logic of calling distant server
    to fetch weather data and store them sparsely on disk.
    """

    def __init__(self):
        self._storage_root = Path(__file__).parent.parent.parent / "storage"

    def storage_root(self):
        return self._storage_root

    def header(self):
        """Header of data stored

        Returns:
            (dict): [unit] description per columns
        """
        pass

    def exists(self, latitude, longitude, year):
        """Check whether file has already been fetched from server

        Args:
            latitude (float): [deg] latitude of place
            longitude (float): [deg] longitude of place
            year (int): [-] year to fetch from YYYY-01-01T00:00 till YYYY-12-31T24:00

        Returns:
            (bool)
        """
        pass


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
        pass

    def fetch(self, latitude, longitude, year):
        """Fetch time series for given location on remote server

        Notes: does nothing if data already in storage

        Args:
            latitude (float): [deg] latitude of place
            longitude (float): [deg] longitude of place
            year (int): [-] year to fetch from YYYY-01-01T00:00 till YYYY-12-31T24:00

        Returns:
            None
        """
        pass
