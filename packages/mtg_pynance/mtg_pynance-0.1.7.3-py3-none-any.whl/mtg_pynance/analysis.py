from pathlib import Path
from typing import Optional
import sqlite3
import polars as pl


def card_stats(database_path: Path, cid: int) -> pl.DataFrame:
    """
    Calculates the market value and gain/loss of the input card using the
    timestamps the prices were recorded in the local SQL database.

    Parameters
    ----------
    database_path: Path
        Path to the local SQL collection database.
    cid: int
        cid of card in collection file.

    Returns
    -------
    pl.DataFrame
        Returns dataframe with schema {"timestamp": pl.String,
        "market_value": pl.Float64, "profit": pl.Float64}.
    """
    # TODO this function assumes that if a card has no price info it has
    # no it has no price table. This is true within the package framework,
    # but may not be if a user pokes around.

    # Connect to local SQL database
    connection: sqlite3.Connection = sqlite3.connect(database_path)
    cursor: sqlite3.Cursor = connection.cursor()

    # Get card's purchase price
    sql_command = f"select price from purchase_price where cid = {cid}"
    purchase_price: Optional[tuple[int, float]] = cursor.execute(sql_command).fetchone()
    if purchase_price is None:
        return f"No records of collection ID {cid} exist in database!"
    purchase_price = float(purchase_price[0])

    # Get card's price data
    sql_command = f"select * from card_{cid}"
    price_data: list[tuple[str, float]] = cursor.execute(sql_command).fetchall()
    card_stats = [
        [timestamp, value, value - purchase_price] for timestamp, value in price_data
    ]

    # Convert stats from list of lists to dataframe
    df = pl.DataFrame(
        card_stats,
        schema={
            "timestamp": pl.String,
            "market_value": pl.Float64,
            "gain/loss": pl.Float64,
        },
        orient="row",
    )

    return df


def collection_stats(database_path: Path) -> pl.DataFrame:
    """
    Calculates the market value and gain/loss of the entire collection of cards
    at the timestamps the prices were recorded in the local SQL database.

    Parameters
    ----------
    database_path: Path
        Path to the local SQL collection database.

    Returns
    -------
    pl.DataFrame
        Returns dataframe with schema {"timestamp": pl.String,
        "market_value": pl.Float64, "profit": pl.Float64}.
    """
    # Connect to local SQL database
    connection: sqlite3.Connection = sqlite3.connect(database_path)
    cursor: sqlite3.Cursor = connection.cursor()

    # Get list of all cards
    sql_command = "select * from purchase_price"
    card_ids: list[tuple[int, float]] = cursor.execute(sql_command).fetchall()
    collection_stats: list[list[str, float, float]] = []

    # Record stats for each card in the local database
    for _, (cid, purchase_price) in enumerate(card_ids):
        sql_command = f"select * from card_{cid}"
        result: list[tuple[str, float]] = cursor.execute(sql_command).fetchall()
        card_stats = [
            [timestamp, value, value - purchase_price] for timestamp, value in result
        ]
        collection_stats.extend(card_stats)

    connection.close()

    # Convert statistics from list of lists to dataframe
    df = pl.DataFrame(
        collection_stats,
        schema={
            "timestamp": pl.String,
            "market_value": pl.Float64,
            "gain/loss": pl.Float64,
        },
        orient="row",
    )

    # Add together cards that have the same timestamp
    df = df.group_by("timestamp").agg(
        pl.col("market_value").sum(), pl.col("gain/loss").sum()
    )

    # TODO ensure that this will always sort correctly because the timestampsa are strings
    # Sort dataframe from earliest to latest timestamps
    df = df.sort("timestamp")

    return df


def collection_extrema(database_path: Path) -> tuple[dict, dict]:
    """
    Calculates the cards in the collection that currently have the largest gain
    and loss.

    Parameters
    ----------
    database_path: Path
        Path to the local SQL collection database.

    Returns
    -------
    tuple[dict, dict]
        Return a tuple of dictionaries where element 0 corresponds to the card
        with the maximum gain and element 1 corresponds to the card with the
        maximum loss. The schema for each dictionary is {"cid": [int], "*": float,
        "purchase_price": float} where * is "gain" or "loss", respectively.

    """
    # Connect to local SQL database
    connection: sqlite3.Connection = sqlite3.connect(database_path)
    cursor: sqlite3.Cursor = connection.cursor()

    # Get list of all cards
    sql_command = "select * from purchase_price"
    card_ids: list[tuple[int, float]] = cursor.execute(sql_command).fetchall()

    gain = {"cid": [], "gain": 0.0, "purchase_price": 0.0}
    loss = {"cid": [], "loss": 0.0, "purchase_price": 0.0}

    for _, (cid, purchase_price) in enumerate(card_ids):
        # Calculate gain/loss of each card with respect to current price
        sql_command = f"select market_value from card_{cid} where timestamp = (select max(timestamp) from card_{cid})"
        current_price = float(cursor.execute(sql_command).fetchone()[0])
        gain_loss = round(current_price - purchase_price, 2)

        # Record card's gain/loss if it is an extreme
        if gain_loss == gain["gain"]:
            gain["cid"].append(cid)

        if gain_loss > gain["gain"]:
            gain["cid"].clear()
            gain["cid"].append(cid)
            gain["gain"] = gain_loss
            gain["purchase_price"] = purchase_price

        if gain_loss == loss["loss"]:
            loss["cid"].append(cid)

        if gain_loss < loss["loss"]:
            loss["cid"].clear()
            loss["cid"].append(cid)
            loss["loss"] = gain_loss
            loss["purchase_price"] = purchase_price

    connection.close()

    return gain, loss


def collection_largest_movers(database_path: Path) -> tuple[dict, dict]:
    """
    Calculates the price movement of each card based on its two most recently recorded
    prices and returns the cards that have the largest and smallest price movement.

    Parameters
    ----------
    database_path: Path
        Path to the local SQL collection database.

    Returns
    -------
    tuple[dict, dict]
        Return a tuple of dictionaries where element 0 corresponds to the card
        with the maximum gain and element 1 corresponds to the card with the
        maximum loss. The schema for each dictionary is {"cid": [int], "*": float,
        "purchase_price": float} where * is "gain" or "loss", respectively.
    """
    # Connect to local SQL database
    connection: sqlite3.Connection = sqlite3.connect(database_path)
    cursor: sqlite3.Cursor = connection.cursor()

    # Get list of all cards
    sql_command = "select * from purchase_price"
    card_ids: list[tuple[int, float]] = cursor.execute(sql_command).fetchall()

    gain = {"cid": [], "gain": 0.0, "purchase_price": 0.0}
    loss = {"cid": [], "loss": 0.0, "purchase_price": 0.0}

    for _, (cid, purchase_price) in enumerate(card_ids):
        sql_command = f"""select market_value - lag(market_value) over (order by timestamp) 
                          from card_{cid} order by timestamp desc limit 1"""
        result: Optional[float] = cursor.execute(sql_command).fetchone()[0]

        if result is None:
            continue

        movement = round(result, 2)

        # Record card's gain/loss if it is an extreme
        if movement == gain["gain"]:
            gain["cid"].append(cid)

        if movement > gain["gain"]:
            gain["cid"].clear()
            gain["cid"].append(cid)
            gain["gain"] = movement
            gain["purchase_price"] = purchase_price

        if movement == loss["loss"]:
            loss["cid"].append(cid)

        if movement < loss["loss"]:
            loss["cid"].clear()
            loss["cid"].append(cid)
            loss["loss"] = movement
            loss["purchase_price"] = purchase_price

    connection.close()

    return gain, loss


def delete_card(database_path: Path, cid: int):
    """
    Deletes card from local SQL database. This includes its
    price table and purchase price information.

    Parameters
    ----------
    database_path: Path
        Path to the local SQL collection database.
    cid: int
        cid of card in collection file.
    """
    # Connect to local SQL database
    connection: sqlite3.Connection = sqlite3.connect(database_path)
    cursor: sqlite3.Cursor = connection.cursor()

    # Delete card's price table from database
    sql_command = f"drop table if exists card_{cid}"
    cursor.execute(sql_command)

    # Delete card's purchase price
    sql_command = f"delete from purchase_price where cid = {cid}"
    cursor.execute(sql_command)

    connection.commit()
    connection.close()
