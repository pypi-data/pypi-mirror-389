from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class Config:
    """
    Class defining the configuration to run mtg_pynance with.

    Parameters
    ----------
    workspace_path: Path
        Path to the workspace directory.
    collection_path: Path
        Path to the card collection csv file.

    Methods
    -------
    create_workspace()
        Creates the workspace folder.
    get_bulk_info_path() -> Path
        Returns the path of Scryfall's bulk data default cards information
        json file.
    get_bulk_data_path() -> Path
        Returns the path of Scryfall's bulk data default cards json file.
    get_database_path() -> Path
        Returns the path to the local SQL collection database.
    get_bulk_data_timestamp() -> Optional[datetime.date]
        Get timestamp of local bulk data files.
    """

    def __init__(self, workspace_path: Path, collection_path: Path) -> None:
        self.workspace_path = workspace_path
        if not collection_path.exists():
            raise Exception("Collection file does not exist at input path!")
        self.collection_path = collection_path

    def create_workspace(self):
        """
        Creates the workspace folder.
        """
        if not self.workspace_path.exists():
            self.workspace_path.mkdir()

    def get_bulk_info_path(self) -> Path:
        """
        Returns the path to Scryfall's bulk data default cards information
        json file.
        """
        path = self.workspace_path / "bulk_default_info.json"
        return path

    def get_bulk_data_path(self) -> Path:
        """
        Returns the path to Scryfall's bulk data default cards json file.
        """
        path = self.workspace_path / "bulk_default_data.json"
        return path

    def get_database_path(self) -> Path:
        """
        Returns the path to the SQL collection database where each card in
        the collection has its information stored.
        """
        path = self.workspace_path / "collection.db"
        return path

    def get_bulk_data_timestamp(self) -> Optional[datetime.date]:
        """
        Get timestamp of local bulk data files if they exist or return
        None if they don't.
        """
        if (
            not self.get_bulk_info_path().exists()
            or not self.get_bulk_data_path().exists()
        ):
            return None

        # Get timestamp of local files
        with open(self.get_bulk_info_path()) as f:
            bulk_info_dict = json.load(f)
        local_ts = bulk_info_dict["updated_at"]
        local_dt = datetime.fromisoformat(local_ts)

        return local_dt
