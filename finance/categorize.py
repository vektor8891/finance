#!/usr/bin/env python

import os
import pprint as pp

import numpy as np
import pandas as pd

import finance.dataframe as d
import finance.functions as f


def match_existing_categories(df: pd.DataFrame, df_cat: pd.DataFrame, year: int) -> pd.DataFrame:
    # add categories
    df = add_category(df, df_cat)

    # export transactions (some might not have a category yet)
    f_path = f.get_path(year, "output", "transactions.xlsx")
    df.sort_values(by=["CategoryName", "Date"], ascending=[False, True], inplace=True)
    df.to_excel(f_path, index=False)
    if d.has_missing_values(df, "CategoryName"):
        raise ValueError(f"Missing categories found in {f_path}. Please fill missing categories manually.")

    return df


def parse_categories_from_transactions(year: int) -> pd.DataFrame:
    import os.path

    f_path = f.get_path(year, "output", "transactions.xlsx")
    cat_cols = ["Priority", "Comment", "CategoryType", "CategoryName", "Pattern"]
    df_cat = pd.DataFrame(columns=cat_cols)

    if os.path.isfile(f_path):
        # parse transactions
        df_all = pd.read_excel(f_path, engine="openpyxl")
        # select rows with category
        df = df_all.loc[~df_all["CategoryName"].isnull(),]
        # if pattern is missing, use transaction details
        df.loc[df["Pattern"].isnull(), "Pattern"] = df["Details"]
        # if priority is missing, use 1
        df.loc[df["Priority"].isnull(), "Priority"] = 1
        # if category type is not provided, use cost
        df.loc[df["CategoryType"].isnull(), "CategoryType"] = "Costs"
        # select relevant columns & remove duplicates
        df_cat = df[cat_cols].drop_duplicates()

    return df_cat


def add_category(df: pd.DataFrame, df_cat: pd.DataFrame) -> pd.DataFrame:
    # check input data
    d.has_column(df, "Details", raise_error=True)
    d.has_duplicates(df_cat, "Pattern", raise_error=True)

    # sort patterns by date (later date ~ higher priority)
    df_cat_sorted = df_cat.sort_values(
        by=["Priority"], ascending=True
    )

    # add empty category columns to transactions data
    for col in df_cat.columns:
        df[col] = 1 if col == "Priority" else ""

    # parse each pattern & assign category
    for _, cat_row in df_cat_sorted.iterrows():

        # logical vectors
        pattern = cat_row["Pattern"]
        has_pattern = df["Details"].str.contains(pattern, regex=False)
        same_priority = df["Priority"] == cat_row["Priority"]
        lower_priority = df["Priority"] < cat_row["Priority"]
        same_category = df["CategoryName"] == cat_row["CategoryName"]
        is_empty = df["CategoryName"] == ""

        # check for multiple match
        df_multi = df[has_pattern & same_priority & ~same_category & ~is_empty]
        if len(df_multi.index) > 0:
            pp.pprint(df_multi)
            raise ValueError("Multiple categories found!")
        else:
            # add category based on pattern
            df.loc[
                has_pattern & (is_empty | lower_priority | same_category),
                df_cat.columns,
            ] = cat_row[df_cat.columns].to_numpy()

    # move details to last column
    df_details = df.pop("Details")
    df["Details"] = df_details

    return df
