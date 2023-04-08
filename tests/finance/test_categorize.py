#!/usr/bin/env python

import numpy as np
import pandas as pd
import pytest

import finance.categorize as c

DF_CAT: pd.DataFrame = pd.DataFrame(
    data={
        "CategoryName": ["Health", "Shopping", "Groceries", "Groceries", "Misc"],
        "Pattern": ["Vaccine", "Amazon", "Food", "Market", "Other"],
        "Priority": [2, 1, 2, 1, 1],
    }
)

COL = "CategoryName"


def test_find_categories(mocker, tmp_path):
    df = pd.DataFrame(data={"Details": ["Market"], "Date": ["2013-01-01"]})
    df_expected = df.copy()
    df_expected["CategoryName"] = "Groceries"
    f_path = tmp_path / "test.xlsx"
    mocker.patch("finance.functions.get_path", return_value=f_path)
    # it should add categories if no category is missing
    df_actual = c.match_existing_categories(df, DF_CAT, 2013)
    assert df_actual["CategoryName"][0] == "Groceries"
    # it should throw error if category is missing
    df_missing = pd.DataFrame(data={"Details": ["Unknown"], "Date": ["2013-01-01"]})
    with pytest.raises(ValueError) as context_info:
        c.match_existing_categories(df_missing, DF_CAT, 2005)
    assert "Missing categories found" in str(context_info.value)
    # it should export rows with missing category
    df_missing.to_excel(f_path, index=False)
    df_actual = pd.read_excel(f_path, engine="openpyxl")
    assert pd.isnull(df_actual["CategoryName"][0])


def test_add_category(tmp_path, mocker):
    # it should throw error if column are missing
    with pytest.raises(ValueError) as context_info:
        c.add_category(pd.DataFrame(), DF_CAT)
    assert "Column 'Details' not found" in str(context_info.value)

    # it should throw error for duplicated patterns
    df = pd.DataFrame(data={"Details": [""]})
    with pytest.raises(ValueError) as context_info:
        c.add_category(df, DF_CAT.append(DF_CAT))
    assert "Duplicates found in Pattern" in str(context_info.value)

    # it should add category based on pattern
    df_ptn = pd.DataFrame(data={"Details": ["Amazon"]})
    df_actual = c.add_category(df_ptn, DF_CAT)
    assert df_actual["CategoryName"][0] == "Shopping"

    # it should overwrite category with higher priority
    df_pry = pd.DataFrame(data={"Details": ["Food from Amazon"]})
    df_actual = c.add_category(df_pry, DF_CAT)
    assert df_actual["CategoryName"][0] == "Groceries"

    # it should throw error if multiple categories found with same priority
    df_mlt = pd.DataFrame(data={"Details": ["Amazon Other"]})
    with pytest.raises(ValueError) as context_info:
        c.add_category(df_mlt, DF_CAT)
    assert "Multiple categories found" in str(context_info.value)
