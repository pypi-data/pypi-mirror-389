from datetime import datetime
from pathlib import Path
from tqdm import tqdm
import requests


def retrieve_bulk_data(
    bulk_info_file: Path, bulk_data_file: Path, timestamp: datetime.date
):
    """
    Write Scryfall's bulk data default cards json file and its information json file
    to the target path. If these files already exist at the target path, they are
    overwritten if the current files hosted by Scryfall are newer.

    Note that Scryfall uses UTC timestamps.

    Parameters
    ----------
    bulk_info_file: Path
        Path to Scryfall's bulk data information file.
    bulk_data_file: Path
        Path to Scryfall's bulk data file.
    timestamp: datetime.date
        Timestamp of local bulk data files.
    """
    # API call to Scryfall for its bulk data default cards information
    scryfall = "https://api.scryfall.com/bulk-data/default-cards"
    bulk_info_r = requests.get(scryfall, params={"format": "json"})
    bulk_info_j = bulk_info_r.json()

    # Check if local files exist and are older than Scryfall's
    if timestamp is not None:
        # Get Scryfall timestamp
        api_ts = bulk_info_j["updated_at"]
        api_dt = datetime.fromisoformat(api_ts)

        if timestamp >= api_dt:
            return

    # Write bulk info file
    with open(bulk_info_file, "wb") as f:
        f.write(bulk_info_r.content)

    # Write bulk data file
    print("Downloading Scryfall's bulk data default cards file...")
    url = bulk_info_j["download_uri"]
    bulk_data_r = requests.get(url, params={"format": "json"}, stream=True)
    bulk_data_j = bulk_info_r.json()
    with tqdm.wrapattr(
        open(bulk_data_file, "wb"),
        "write",
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
        miniters=1,
        total=bulk_data_j["size"],
    ) as fout:
        for chunk in bulk_data_r.iter_content(chunk_size=4096):
            fout.write(chunk)
