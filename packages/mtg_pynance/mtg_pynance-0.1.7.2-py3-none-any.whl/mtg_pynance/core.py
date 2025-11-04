from mtg_pynance.config import Config
from mtg_pynance.logger import make_logger, logger_error
from mtg_pynance.retrieval import retrieve_bulk_data
from mtg_pynance.collection import load_collection
from typing import Optional
from datetime import datetime
from pathlib import Path
import polars as pl
import numpy as np
import sqlite3

FOIL_TYPE = {"none": "usd", "foil": "usd_foil", "etched": "usd_etched"}


def record_card_entry(
    bulk_data: pl.DataFrame,
    collection: pl.LazyFrame,
    cid: int,
    timestamp: datetime.date,
    cursor: sqlite3.Cursor,
):
    """
    Records a card from the collection csv in the local SQL database. It writes the purchase price
    and cid of the card to the purchase_price table in the database. It records the card's price and
    timestamp from the local Scryfall bulk data file to the card's table in the database, making it
    if it does not exist.

    Parameters
    ----------
    bulk_data: pl.DataFrame
        Dataframe of Scryfall bulk data.
    collection: pl.LazyFrame
        Lazyframe of input collection file.
    cid: int
        cid of card in collection file.
    timestamp: datetime.date
        Timestamp of local bulk data files.
    cursor: sqlite3.Cursor
        Cursor over the local collection database.
    """
    # Card info from collection file
    id: str = collection.filter(pl.col("cid") == cid).collect().select("id").item()
    foiling: str = (
        collection.filter(pl.col("cid") == cid).collect().select("foiling").item()
    )
    purchase_price: float = (
        collection.filter(pl.col("cid") == cid)
        .collect()
        .select("purchase_price")
        .item()
    )

    # TODO SQL seems to be slightly faster, should check more
    # a = bulk_data.row(by_predicate=(pl.col("id") == id), named=True)["prices"][foilkey]

    # Retrieve card's price data from bulk data file
    price_df: pl.DataFrame = bulk_data.sql(f"select prices from self where id = '{id}'")
    if price_df.height == 0:
        logger_error(
            __name__, f"Collection ID {cid}: ID does not exist in Scryfall database!"
        )
        return
    price_dict: dict[str, float] = price_df.item()

    # Retrieve card's price
    current_price: Optional[float] = price_dict[FOIL_TYPE[foiling]]
    if current_price is None:
        logger_error(
            __name__,
            f"Collection ID {cid}: Foil type has no price in Scryfall database!",
        )
        return

    # Add card's purchase price to purchase_price table, if nonexistent
    sql_command = "insert or ignore into purchase_price values (?, ?)"
    cursor.execute(sql_command, (int(cid), purchase_price))

    # Create card's table in dataframe, if nonexistent
    table_name = "card_" + str(cid)
    sql_command = f"create table if not exists {table_name} (timestamp string unique, market_value float)"
    cursor.execute(sql_command)

    # Insert card statistics into its table, if nonexistent
    sql_command = f"insert or ignore into {table_name} values (?, ?)"
    cursor.execute(
        sql_command,
        (timestamp.isoformat(), current_price),
    )


def make_collection_db(
    database_path: Path,
    bulk_data: pl.DataFrame,
    collection: pl.LazyFrame,
    timestamp: datetime.date,
):
    """
    Makes local collection database where all card price information is stored.

    Parameters
    ----------
    database_path: Path
        Path to SQL collection database.
    bulk_data: pl.DataFrame
        Dataframe of Scryfall bulk data.
    collection: pl.LazyFrame
        Lazyframe of input collection file.
    timestamp: datetime.date
        Timestamp of local bulk data files.
    """
    # Connect to local SQL database, if nonexistent
    connection: sqlite3.Connection = sqlite3.connect(database_path)
    cursor: sqlite3.Cursor = connection.cursor()

    # Make table of purchase prices, if nonexistent
    sql_command = (
        "create table if not exists purchase_price (cid int unique, price float)"
    )
    cursor.execute(sql_command)

    # Record entry for each card in collection
    cid_array: np.ndarray = (
        collection.select(pl.col("cid")).collect().to_numpy().flatten()
    )
    for cid in cid_array:
        record_card_entry(bulk_data, collection, cid, timestamp, cursor)

    connection.commit()
    connection.close()


def run_mtg_pynance(config: Config):
    """
    Main function of mtg_pynance. It creates the workspace, retrieves the bulk data,
    imports the collection and bulk data files, and records the price information
    of each card in the collection to the local database.


    Parameters
    ----------
    config: mtg_pynance.config.Config
        Configuration to run mtg_pynance with.
    """
    config.create_workspace()
    print("Workspace validated.")

    make_logger(config.workspace_path)
    print("Logger initialized.")

    # Determine if local bulk data files exist and get their timestamp
    local_dt: datetime.date = config.get_bulk_data_timestamp()

    retrieve_bulk_data(
        config.get_bulk_info_path(), config.get_bulk_data_path(), local_dt
    )

    # Get timestamp of bulk data files
    local_dt: datetime.date = config.get_bulk_data_timestamp()

    print("Importing collection and bulk data files...")
    collection: pl.LazyFrame = load_collection(config.collection_path)
    bulk_data: pl.DataFrame = pl.read_json(
        config.get_bulk_data_path(), infer_schema_length=None
    )
    print("Collection and bulk data files imported.")

    make_collection_db(config.get_database_path(), bulk_data, collection, local_dt)
    print("The Tolarian Academy has written the record!")
