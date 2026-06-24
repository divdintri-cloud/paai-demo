import os
from pathlib import Path


def get_active_data_dir():
    data_dir = Path(os.getenv("PAAI_DATA_DIR", "data"))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_books_inventory_path():
    return get_active_data_dir() / "books_inventory.csv"


class DynamicBooksInventoryPath:
    """
    Path-like object that always resolves to the current active user's books file.
    This avoids stale import-time paths when Streamlit switches users.
    """

    def _path(self):
        return get_books_inventory_path()

    def __fspath__(self):
        return str(self._path())

    def __str__(self):
        return str(self._path())

    def __repr__(self):
        return str(self._path())

    def __getattr__(self, name):
        return getattr(self._path(), name)


DYNAMIC_BOOKS_INVENTORY_PATH = DynamicBooksInventoryPath()
