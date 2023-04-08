#!/usr/bin/env python

import datetime as dt
from datetime import date

import numpy as np
import pandas as pd
import pytest

import finance.dataframe
import finance.dataframe as d
import finance.parser

DF: pd.DataFrame = pd.DataFrame(
    data={"Name": ["Alex", "Eve"], "Age": [12, 14]}
)

COL = "Name"


def compare_col(df: pd.DataFrame, col_name: str, values: list) -> bool:
    return list(df[col_name].values) == values


def test_strip_col_names():
    df_mod = DF.copy()
    first_col = DF.columns[0]
    df_mod.rename(columns={first_col: f"    {first_col}     "}, inplace=True)
    assert d.strip_col_names(df_mod).equals(DF)


def test_add_column():
    df_mod = DF.copy()
    df_mod["New Column"] = "Value"
    assert d.add_column(DF, "New Column", "Value").equals(df_mod)


def test_match_pattern():
    df_pattern = d.match_pattern(
        DF.copy(),
        new_column="Initial",
        pattern_column="Name",
        pattern="^[A-Z]",
    )
    assert compare_col(df_pattern, "Initial", ["A", "E"])


def test_convert_type():
    df_float = d.convert_type(DF.copy(), column="Age", col_type="str")
    assert compare_col(df_float, "Age", ["12", "14"])


def test_replace_value():
    df_replace = d.replace_value(
        df=DF.copy(), column="Name", value_from="lex", value_to="dam"
    )
    assert compare_col(df_replace, "Name", ["Adam", "Eve"])
    df_replace = d.replace_value(
        df=DF.copy(),
        column="Name",
        value_from="[a-z]*",
        value_to="",
        regex=True,
    )
    assert compare_col(df_replace, "Name", ["A", "E"])


def test_rename_column():
    df_old = pd.DataFrame(columns=["Old"])
    df_new = pd.DataFrame(columns=["New"])
    assert d.rename_column(df_old, "Old", "New").equals(df_new)


def test_merge_columns():
    df_merged = d.merge_columns(
        DF.copy(), column="NameAge", col_list=["Name", "Age"]
    )
    assert compare_col(df_merged, "NameAge", ["Alex 12", "Eve 14"])
    df_merged_same = d.merge_columns(
        DF.copy(), column="Age", col_list=["Name", "Age"]
    )
    assert compare_col(df_merged_same, "Age", ["Alex 12", "Eve 14"])


def test_multiple_column():
    df_multiplied = d.multiple_column(DF.copy(), column="Age", multiplier=2)
    assert compare_col(df_multiplied, "Age", [24, 28])


def test_fill_column():
    df_na = pd.DataFrame([[np.nan]], columns=["Col"])
    # it should throw error if column is missing
    with pytest.raises(ValueError) as context_info:
        d.fill_column(df_na, column="Unknown", value=0)
    assert "Column 'Unknown' not found" in str(context_info.value)
    # it should fill column with value
    df_na_expected = d.fill_column(df_na, column="Col", value=0)
    assert compare_col(df_na_expected, "Col", [0])


def test_fill_columns():
    df_na = pd.DataFrame([[np.nan, ""]], columns=["Col1", "Col2"])
    # it should throw error if column is missing
    with pytest.raises(ValueError) as context_info:
        d.fill_columns(df_na, columns=["Col1", "Col3"], value=0)
    assert "Column 'Col3' not found" in str(context_info.value)
    # it should fill columns with value
    df_na_expected = d.fill_columns(df_na, columns=["Col1", "Col2"], value=0)
    assert compare_col(df_na_expected, "Col1", [0])
    assert compare_col(df_na_expected, "Col2", [0])


def test_summarize_columns():
    df_sum = DF.copy()
    df_sum["Height (cm)"] = [150, 156]
    df_sum = d.summarize_columns(
        df_sum, column="Age + Height", col_list=["Age", "Height (cm)"]
    )
    assert compare_col(df_sum, "Age + Height", [162, 170])


def test_format_date():
    df_date = DF.copy()
    df_date["DOB"] = ["1/2/2008", "4/13/2006"]
    df_date = d.format_date(df_date, "DOB", "%m/%d/%Y")
    assert compare_col(df_date, "DOB", [date(2008, 1, 2), date(2006, 4, 13)])


def test_filter_columns():
    df_filter = DF.copy()
    df_filter = d.filter_columns(df_filter, col_list=["Name"])
    assert df_filter.equals(DF[["Name"]])


def test_has_duplicates():
    assert not d.has_duplicates(DF, "Name", raise_error=True)
    df_duplicate = DF.copy().append(DF)
    with pytest.raises(ValueError) as context_info:
        d.has_duplicates(df_duplicate, "Name", raise_error=True)
    assert "Duplicates found" in str(context_info.value)


def test_get_missing_values():
    # it should throw error if Category column is missing
    with pytest.raises(ValueError) as context_info:
        d.get_missing_values(pd.DataFrame(), COL)
    assert f"Column '{COL}' not found" in str(context_info.value)
    # it should return rows with missing category
    df_missing = pd.DataFrame(data={COL: [""]})
    assert d.get_missing_values(df_missing, COL).equals(df_missing)
    # it should return empty df if no category is missing
    df_no_missing = pd.DataFrame(data={COL: ["C"]})
    assert d.get_missing_values(df_no_missing, COL).empty
    # it should work with nan values
    df_nan = pd.DataFrame(data={COL: [np.nan]})
    assert d.get_missing_values(df_nan, COL).equals(df_nan)


def test_has_missing_values():
    # it should throw error if column doesn't exist
    with pytest.raises(ValueError) as context_info:
        d.has_missing_values(pd.DataFrame(), COL)
    assert f"Column '{COL}' not found" in str(context_info.value)
    # it should return True if column values are missing
    df_missing = pd.DataFrame(data={COL: [""]})
    assert d.has_missing_values(df_missing, COL)
    # it should throw error if column values missing and error flag is on
    with pytest.raises(ValueError) as context_info:
        d.has_missing_values(df_missing, COL, raise_error=True)
    assert f"Missing values in '{COL}'" in str(context_info.value)
    # it should return False if no value is missing in column
    df_no_missing = pd.DataFrame(data={COL: ["C"]})
    assert not d.has_missing_values(df_no_missing, COL, raise_error=True)


def test_has_columns():
    # it should return True if every column exist
    assert d.has_columns(DF, ["Name", "Age"])
    # it should return False if any column is missing
    assert not d.has_columns(DF, ["Name", "Unknown"])
    # it should throw error if any column is missing and error flag is on
    with pytest.raises(ValueError) as context_info:
        d.has_columns(DF, ["Name", "Unknown"], True)
    assert "Column 'Unknown' not found" in str(context_info.value)


def test_has_column():
    # it should return True if column exist
    assert d.has_column(DF, COL)
    # it should return False if column doesn't exist
    assert not d.has_column(DF, "Unknown")
    # it should throw error if column is missing and error flag is on
    with pytest.raises(ValueError) as context_info:
        d.has_column(DF, "Unknown", True)
    assert "Column 'Unknown' not found" in str(context_info.value)


def test_parse_csv(tmp_path, mocker):
    # it should parse categories and patterns
    f_path = tmp_path / "test.csv"
    DF.to_csv(f_path, index=False)
    mocker.patch("finance.functions.get_path", return_value=f_path)
    assert finance.dataframe.parse_csv(2013, "folder", "file").equals(DF)


def test_unique_values():
    # it should throw error if column is missing
    with pytest.raises(ValueError) as context_info:
        d.unique_values(DF, "Unknown")
    assert "Column 'Unknown' not found" in str(context_info.value)
    # it should return unique values for column
    df_duplicated = DF.append(DF)
    unique_names = d.unique_values(df_duplicated, "Name")
    assert unique_names == ["Alex", "Eve"]


def test_filter_value():
    # it should filter column by value
    assert d.filter_value(DF, "Name", "Alex").equals(DF.head(1))
    # it should throw error if value not found and error flag is on
    with pytest.raises(ValueError) as context_info:
        d.filter_value(DF, "Name", "Joe", raise_error=True)
    assert "No 'Joe' found in column 'Name'" in str(context_info.value)


def test_filter_values():
    # it should filter columns by values
    assert d.filter_values(DF, {"Name": "Alex", "Age": 12}).equals(DF.head(1))
    # it should throw error if values not found and error flag is on
    with pytest.raises(ValueError) as context_info:
        d.filter_values(DF, {"Name": "Joe"}, raise_error=True)
    assert "No 'Joe' found in column 'Name'" in str(context_info.value)


def test_filter_date():
    # it should throw error if date column is missing
    with pytest.raises(ValueError) as context_info:
        d.filter_date(DF, dt.date.today())
    assert "Column 'Date' not found" in str(context_info.value)
    # it should filter date
    df_date = pd.DataFrame(data={"Date": [dt.date(2013, 1, 20)]})
    assert d.filter_date(df_date, dt.date(2013, 1, 19)).empty
    assert d.filter_date(df_date, dt.date(2013, 1, 20)).equals(df_date)
