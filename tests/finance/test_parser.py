#!/usr/bin/env python

import datetime as dt

import numpy as np
import pandas as pd
import pytest

import finance.parser as prs

DF: pd.DataFrame = pd.DataFrame(
    data={"Name": ["Alex", "Eva"], "Age": [12, 14]}
)


def test_parser_init():
    # it should create object
    parser = prs.Parser(2012, "file.csv", "EUR")
    assert parser.year == 2012
    assert parser.file_name == "file.csv"
    assert parser.account_name == "file"
    assert parser.currency == "EUR"
    # it should create with default currency
    parser = prs.Parser(2012, "file")
    assert parser.currency == "USD"


def test_parser_read(tmp_path, mocker):
    # it should parse csv file
    f_path_csv = tmp_path / "input.csv"
    DF.to_csv(f_path_csv, index=False)
    mocker.patch("finance.functions.get_path", return_value=str(f_path_csv))
    parser = prs.Parser(2012, "file", "account")
    assert parser.read().equals(DF)
    # it should parse xls/xlsx
    f_path_xls = tmp_path / "input.xls"
    DF.to_excel(f_path_xls, index=False, engine='xlwt')
    mocker.patch("finance.functions.get_path", return_value=str(f_path_xls))
    parser = prs.Parser(2012, "file", "account")
    assert parser.read().equals(DF)


def test_parser_transform(mocker):
    mocker.patch("finance.dataframe.add_column", return_value=DF)
    mocker.patch("finance.dataframe.format_date", return_value=DF)
    mocker.patch("finance.dataframe.filter_columns", return_value=DF)
    mocker.patch("finance.dataframe.merge_columns", return_value=DF)
    mocker.patch("finance.dataframe.replace_value", return_value=DF)
    parser = prs.Parser(2011, "file.csv")
    assert parser.transform(DF).equals(DF)
    mocker.patch("finance.dataframe.match_pattern", return_value=DF)
    mocker.patch("finance.dataframe.replace_value", return_value=DF)
    mocker.patch("finance.dataframe.convert_type", return_value=DF)
    mocker.patch("finance.dataframe.rename_column", return_value=DF)
    mocker.patch("finance.dataframe.merge_columns", return_value=DF)
    mocker.patch("finance.dataframe.filter_value", return_value=DF)
    unicredit_parser = prs.UnicreditParser(2011, "file.csv")
    assert unicredit_parser.transform(DF).equals(DF)
    mocker.patch("finance.dataframe.fill_columns", return_value=DF)
    mocker.patch("finance.dataframe.multiple_column", return_value=DF)
    mocker.patch("finance.dataframe.summarize_columns", return_value=DF)
    capitalone_parser = prs.CapitalOneParser(2012, "file.xlsx")
    assert capitalone_parser.transform(DF).equals(DF)
    hsbc_credit_parser = prs.HSBCMasterCardParser(2012, "file.xlsx")
    assert hsbc_credit_parser.transform(DF).equals(DF)
    hsbc_parser = prs.HSBCParser(2012, "file.xlsx")
    assert hsbc_parser.transform(DF).equals(DF)
    wise_parser = prs.WiseParser(2012, "file.xlsx")
    assert wise_parser.transform(DF).equals(DF)


def test_parser_parse(mocker):
    mocker.patch("finance.parser.Parser.read", return_value=DF)
    mocker.patch("finance.parser.Parser.transform", return_value=DF)
    mocker.patch("finance.parser.Parser.validate", return_value=None)
    parser = prs.Parser(2016, "file.csv")
    assert parser.parse().equals(DF)


def test_parser_equal():
    # it should return false if classes are different
    parser0 = pd.DataFrame()
    parser1 = prs.Parser(2011, "file.csv")
    assert parser1 != parser0
    # it should return true if all attributes match
    parser2 = prs.Parser(2011, "file.csv")
    assert parser1 == parser2
    # it should return false if year doesn't match
    parser3 = prs.Parser(2021, "file.csv")
    assert parser1 != parser3
    # it should return false if file name doesn't match
    parser4 = prs.Parser(2011, "file.xlsx")
    assert parser1 != parser4
    # it should return false if currency doesn't match
    parser5 = prs.Parser(2011, "file.csv", "EUR")
    assert parser1 != parser5


def test_parser_validate():
    parser = prs.Parser(2013, "file")
    cols = ["Date", "Account", "Amount", "Currency", "Details"]
    df_empty = pd.DataFrame(columns=cols)
    # it should throw error if df is empty
    with pytest.raises(ValueError) as context_info:
        parser.validate(df_empty)
    assert "Empty dataframe" in str(context_info.value)
    # it should throw error if any column is missing
    df = pd.DataFrame([[0, 1, 2, 3, 4]], columns=cols)
    for col in cols:
        df_no_col = df.copy()
        del df_no_col[col]
        with pytest.raises(ValueError) as context_info:
            parser.validate(df_no_col)
        assert f"Column '{col}' not found" in str(context_info.value)
    # it should throw error if there is extra column
    df_extra = df.copy()
    df_extra["Extra"] = ""
    with pytest.raises(ValueError) as context_info:
        parser.validate(df_extra)
    assert "Extra columns" in str(context_info.value)
    # it should throw error if there are missing values
    for col in cols:
        df_missing = df.copy()
        df_missing.loc[0, col] = np.nan
        with pytest.raises(ValueError) as context_info:
            parser.validate(df_missing)
        assert f"Missing values in '{col}'" in str(context_info.value)
    # it should throw error if it contains data for different year
    df_year = df.copy()
    df_year.loc[0, "Date"] = dt.date(2012, 12, 1)
    with pytest.raises(ValueError) as context_info:
        parser.validate(df_year)
    assert "Invalid year 2012 found" in str(context_info.value)
    # it should return None if no column is missing and date is correct
    df_correct = df.copy()
    df_correct.loc[0, "Date"] = dt.date(2013, 12, 1)
    assert parser.validate(df_correct) is None


def test_unicredit_parser_init():
    # it should initialize
    parser = prs.UnicreditParser(1988, "unicredit.csv")
    assert parser.year == 1988
    assert parser.file_name == "unicredit.csv"
    assert parser.account_name == "unicredit"
    assert parser.currency == "HUF"


def test_capital_one_parser_init():
    # it should initialize parser
    credit_parser = prs.CapitalOneParser(1988, "capitalone.csv")
    assert credit_parser.year == 1988
    assert credit_parser.file_name == "capitalone.csv"
    assert credit_parser.account_name == "capitalone"
    assert credit_parser.currency == "USD"


def test_hsbc_parser_init():
    # it should initialize
    parser = prs.HSBCParser(1988, "hsbc.csv")
    parser_credit = prs.HSBCMasterCardParser(1988, "hsbc.csv")
    assert parser.year == parser_credit.year == 1988
    assert parser.file_name == parser_credit.file_name == "hsbc.csv"
    assert parser.account_name == parser_credit.account_name == "hsbc"
    assert parser.currency == parser_credit.currency == "USD"


def test_wise_parser_init():
    # it should initialize
    parser = prs.WiseParser(1988, "wise.csv")
    assert parser.year == 1988
    assert parser.file_name == "wise.csv"
    assert parser.account_name == "wise"
    assert parser.currency == "USD"


def test_get_parser_object():
    # it should parse unicredit transaction file
    unicredit_parser_obj = prs.UnicreditParser(1998, "Unicredit_Checking.xls")
    assert (
        prs.get_parser_object(1998, "Unicredit_Checking.xls")
        == unicredit_parser_obj
    )
    # it should parse cash transaction file
    cash_parser_obj = prs.Parser(1998, "Cash.csv")
    assert prs.get_parser_object(1998, "Cash.csv") == cash_parser_obj
    # it should parse capital one transaction file
    capitalone_parser = prs.CapitalOneParser(1998, "CapitalOne.csv")
    assert prs.get_parser_object(1998, "CapitalOne.csv") == capitalone_parser
    # it should parse hsbc mastercard file
    hsbc_credit_parser = prs.HSBCMasterCardParser(2003, "HSBC_Mastercard.csv")
    assert (
        prs.get_parser_object(2003, "HSBC_Mastercard.csv")
        == hsbc_credit_parser
    )
    # it should parse regular hsbc file
    hsbc_parser = prs.HSBCParser(2005, "HSBC.csv")
    assert prs.get_parser_object(2005, "HSBC.csv") == hsbc_parser
    # it should parse transferwise file
    wise_parser = prs.WiseParser(2005, "Wise.csv")
    assert prs.get_parser_object(2005, "Wise.csv") == wise_parser
    # it should throw error for invalid file
    with pytest.raises(ValueError) as context_info:
        prs.get_parser_object(1998, "unknown_file.xls")
    assert "Cannot find parser object" in str(context_info.value)


class MockObj:
    @staticmethod
    def parse():
        return DF


def test_parse_transaction_file(mocker):
    # it should parse transaction file
    mocker.patch("finance.parser.get_parser_object", return_value=MockObj)
    assert prs.parse_transaction_file(2033, "file.txt").equals(DF)


def test_parse_transactions(mocker):
    mocker.patch("finance.parser.parse_transaction_file", return_value=DF)
    # it should parse single file
    mocker.patch(
        "finance.functions.get_transaction_files", return_value=["f1"]
    )
    assert prs.parse_transactions(2003).equals(DF)
    # it should parse multiple files
    mocker.patch(
        "finance.functions.get_transaction_files", return_value=["f1", "f2"]
    )
    df_appended = DF.copy().append(DF, ignore_index=True)
    assert prs.parse_transactions(2004).equals(df_appended)
