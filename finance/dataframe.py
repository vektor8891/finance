#!/usr/bin/env python

import datetime as dt
import re
from typing import Union

import numpy as np
import pandas as pd

import finance.functions as f


def strip_col_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    return df


def add_column(df: pd.DataFrame, column: str, value: str) -> pd.DataFrame:
    df[column] = value
    return df


def match_pattern(
    df: pd.DataFrame, new_column: str, pattern_column: str, pattern: str
) -> pd.DataFrame:
    dfc = df.copy()
    dfc.loc[:, new_column] = dfc[pattern_column].apply(
        lambda x: "".join(re.findall(pattern, x))
    )
    return dfc


def convert_type(df: pd.DataFrame, column: str, col_type: str) -> pd.DataFrame:
    dfc = df.copy()
    df.loc[:, column] = dfc[column].astype(col_type)
    return df


def replace_value(
    df: pd.DataFrame, column: str, value_from: str, value_to: str, regex=False
) -> pd.DataFrame:
    dfc = df.copy()
    dfc[column] = dfc[column].astype(str)
    df.loc[:, column] = dfc[column].str.replace(
        value_from, value_to, regex=regex
    )
    return df


def rename_column(
    df: pd.DataFrame, column_old: str, column_new: str
) -> pd.DataFrame:
    return df.rename(columns={column_old: column_new})


def merge_columns(
    df: pd.DataFrame, column: str, col_list: list
) -> pd.DataFrame:
    dfc = df.copy()
    dfd = df[col_list].copy()
    dfc.loc[:, column] = dfd.apply(
        lambda x: " ".join([str(v) for v in x]), axis=1
    )
    return dfc


def multiple_column(
    df: pd.DataFrame, column: str, multiplier: int
) -> pd.DataFrame:
    df.loc[:, column] *= multiplier
    return df


def fill_column(
    df: pd.DataFrame, column: str, value: Union[int, str]
) -> pd.DataFrame:
    has_column(df, column, raise_error=True)
    df.replace("", np.nan, inplace=True)
    dfc = df.copy()
    mask = dfc[column].isnull()
    dfc.loc[mask, column] = value
    return dfc


def fill_columns(
    df: pd.DataFrame, columns: list, value: Union[int, str]
) -> pd.DataFrame:
    for column in columns:
        df = fill_column(df, column, value)
    return df


def summarize_columns(
    df: pd.DataFrame, column: str, col_list: list
) -> pd.DataFrame:
    df[column] = df[col_list].apply(lambda x: sum(x), axis=1)
    return df


def format_date(df: pd.DataFrame, column: str, date_format: str):
    df[column] = pd.to_datetime(df[column], format=date_format).dt.date
    return df


def filter_columns(df: pd.DataFrame, col_list: list) -> pd.DataFrame:
    valid_columns = [v for v in col_list if v in df.columns]
    return df[valid_columns]


def has_duplicates(df: pd.DataFrame, column: str, raise_error=False) -> bool:
    df_duplicate = df[df.duplicated([column])]
    has_duplicate = not df_duplicate.empty
    if has_duplicate & raise_error:
        raise ValueError(f"Duplicates found in {column}:", df_duplicate)
    return has_duplicate


def get_missing_values(df: pd.DataFrame, column: str) -> pd.DataFrame:
    has_column(df, column, raise_error=True)
    return df[(df[column] == "") | (df[column].isnull())]


def has_missing_values(
    df: pd.DataFrame, column: str, raise_error=False
) -> bool:
    df_missing = get_missing_values(df, column)
    has_missing = len(df_missing.index) > 0
    if has_missing & raise_error:
        print(df_missing)
        raise ValueError(f"Missing values in '{column}'")
    else:
        return has_missing


def has_columns(df: pd.DataFrame, columns: list, raise_error=False) -> bool:
    return all([has_column(df, c, raise_error) for c in columns])


def has_column(df: pd.DataFrame, column: str, raise_error=False) -> bool:
    has_col = column in df.columns
    if raise_error and not has_col:
        raise ValueError(f"Column '{column}' not found!")
    return has_col


def parse_csv(year: int, folder: str, file_name: str) -> pd.DataFrame:
    f_path = f.get_path(year, folder, file_name)
    df = pd.read_csv(f_path, encoding="utf-8")
    df = strip_col_names(df)
    return df


def unique_values(df: pd.DataFrame, column: str) -> list:
    has_column(df, column, raise_error=True)
    values = df[column].unique()
    return list(values)


def filter_value(
    df: pd.DataFrame, column: str, value: str, raise_error=False
) -> pd.DataFrame:
    has_column(df, column, raise_error=True)
    df_filter = df[df[column] == value]
    if df_filter.empty & raise_error:
        raise ValueError(f"No '{value}' found in column '{column}'")
    return df_filter


def filter_values(
    df: pd.DataFrame, filter_dict: dict, raise_error=False
) -> pd.DataFrame:
    for column, value in filter_dict.items():
        df = filter_value(df, column, value, raise_error)
    return df


def filter_date(df: pd.DataFrame, date_object: dt.date):
    has_column(df, "Date", raise_error=True)
    return df[df["Date"] <= date_object]
