from pathlib import Path
import polars as pl
import textwrap


def is_collection_valid(collection: pl.LazyFrame):
    """
    Checks input collection file for compliance to prevent code breaking downstream.
    This is almost certainly not exhaustive.

    Parameters
    ----------
    collection: pl.LazyFrame
        Lazyframe of input collection file.
    """
    num_cards: int = collection.select(pl.count()).collect().item()

    if collection.select(pl.col("cid")).count().collect().item() != num_cards:
        raise Exception(
            "Some cards are missing collection ID's! Check collection file!"
        )

    if (
        collection.select(pl.col("cid")).collect().unique(keep="any").height
        != num_cards
    ):
        raise Exception(
            "Not every card has a unique collection ID! Check collection file!"
        )

    # Note that polars seems to default interpret ints as int64
    schema = {
        "cid": pl.Int64,
        "id": pl.String,
        "foiling": pl.String,
        "purchase_price": pl.Float64,
    }
    if collection.collect_schema() != schema:
        raise Exception(
            textwrap.fill(
                f"""Some or all of the required columns in the collection file are not of the correct
                    data type. The required columns and their data types are {schema}."""
            )
        )

    if collection.select(pl.col("foiling")).count().collect().item() != num_cards:
        raise Exception("Some cards are missing foil types! Check collection file!")

    foil_types = ["none", "foil", "etched"]
    if (
        collection.filter(pl.col("foiling").is_in(foil_types)).collect().height
        != num_cards
    ):
        raise Exception("Some cards have invalid foil types! Check collection file!")

    if collection.select(pl.col("id")).count().collect().item() != num_cards:
        raise Exception("Some cards are missing ID's! Check collection file!")

    if (
        collection.select(pl.col("purchase_price")).count().collect().item()
        != num_cards
    ):
        raise Exception(
            "Some cards are missing purchase prices! Check collection file!"
        )


def load_collection(collection_path: Path):
    """
    Loads card collection csv file as lazyframe and checks if it is valid.

    Parameters
    ----------
    collection_path: Path
        Path to the card collection csv file.
    """
    collection_lf: pl.LazyFrame = pl.scan_csv(collection_path)
    collection_lf: pl.LazyFrame = collection_lf.select(
        "cid", "id", "foiling", "purchase_price"
    )
    is_collection_valid(collection_lf)

    return collection_lf
