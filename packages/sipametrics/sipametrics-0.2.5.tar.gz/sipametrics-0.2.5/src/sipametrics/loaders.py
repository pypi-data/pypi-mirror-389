import collections.abc
import pandas as pd
import pathlib
import typing
import sipametrics.models.direct_alpha as direct_alpha_models


def _load_csv(file_path: typing.Union[str, pathlib.Path], field_names: typing.Optional[list[str]]=None, date_fields: typing.Optional[list[str]]=None) -> pd.DataFrame:
    kwargs = {}
    if field_names:
        kwargs["usecols"] = field_names
    if date_fields:
        kwargs["parse_dates"] = date_fields

    df = pd.read_csv(file_path, **kwargs)
    return df

def _sniff_csv(file_path: typing.Union[str, pathlib.Path], field_names: list[str]) -> list[str]: 
    with open(file_path, "r") as f:
        headline = f.readline().strip().split(",")

    headers = { column.lower() for column in headline }
    columns = [ column for column in field_names if column.lower() in headers ]
    return columns
    

def load_fund_datapoints(file_path: typing.Union[str, pathlib.Path]) -> list[direct_alpha_models.FundDatapoint]:
    """
    Loads fund datapoints from a CSV file, and returns the rows as a list of FundDatapoint objects. Note that first row of the file must contain the following fields:
    date, contribution, distribution.

    Args:
        file_path (str, Path): Path to the CSV file.

    Returns:
        list (FundDatapoint): List of FundDatapoint objects, encapsulating entries of date, contribution and distribution.
    """
    field_names = _sniff_csv(file_path, field_names=["date", "contribution", "distribution"])
    date_fields = ["date"]

    df = _load_csv(file_path=file_path, field_names=field_names, date_fields=date_fields)
    records = typing.cast(collections.abc.Sequence[dict[str, typing.Any]], df.to_dict(orient="records"))
    datapoints = [direct_alpha_models.FundDatapoint(**row) for row in records]
    return datapoints

def load_index_benchmark_datapoints(file_path: typing.Union[str, pathlib.Path]) -> list[direct_alpha_models.IndexBenchmarkDatapoint]:
    """
    Loads index benchmark datapoints from a CSV file, and returns the rows as a list of IndexBenchmarkDatapoint objects. Note that first row of the file must contain
    the following fields: date, level.

    Args:
        file_path (str, Path): Path to the CSV file.

    Returns:
        list (IndexBenchmarkDatapoint): List of IndexBenchmarkDatapoint objects, encapsulating entries of date and (index) level.
    """
    field_names = _sniff_csv(file_path, field_names=["date", "level"])
    date_fields = ["date"]

    df = _load_csv(file_path=file_path, field_names=field_names, date_fields=date_fields)
    records = typing.cast(collections.abc.Sequence[dict[str, typing.Any]], df.to_dict(orient="records"))
    datapoints = [direct_alpha_models.IndexBenchmarkDatapoint(**row) for row in records]
    return datapoints
