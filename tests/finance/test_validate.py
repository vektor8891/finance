#!/usr/bin/env python

import datetime as dt
import json

import numpy as np
import pandas as pd
import pytest

import finance.validate as v

DF_ACCOUNT = pd.DataFrame(
    data={
        "Account": ["Cash", "Cash", "Bank"],
        "InitialBalance": [1000, 10, 345.3],
        "Currency": ["HUF", "EUR", "USD"],
    }
)

DF = pd.DataFrame(
    data={
        "Date": [dt.date(2012, 12, 1), dt.date(2012, 11, 6)],
        "Account": ["Cash", "Bank"],
        "Category": ["Groceries", "Transfer"],
        "Amount": [123.2, -100],
        "Currency": ["EUR", "USD"],
    }
)


def test_get_balances(mocker):
    # it should return None if no column/value is missing
    df = pd.DataFrame([range(5)], columns=v.COLS_BALANCE)
    mocker.patch("finance.dataframe.parse_csv", return_value=df)
    mocker.patch("finance.validate.get_initial_balance", return_value=0)
    mocker.patch("finance.validate.get_pnl", return_value=0)
    # mocker.patch("finance.validate.compare_balances", return_value=None)
    assert v.get_balances(2014).equals(df)

    for col in v.COLS_BALANCE:

        # it should throw error if column has missing values
        df_missing = df.copy()
        df_missing.loc[0, col] = np.nan
        mocker.patch("finance.dataframe.parse_csv", return_value=df_missing)
        mocker.patch("finance.dataframe.fill_column", return_value=df_missing)
        with pytest.raises(ValueError) as context_info:
            v.get_balances(2014)
        assert f"Missing values in '{col}'" in str(context_info.value)

        # it should throw error if column is missing
        del df_missing[col]
        with pytest.raises(ValueError) as context_info:
            v.get_balances(2014)
        assert f"Column '{col}' not found" in str(context_info.value)


def test_check_monthly_balances(mocker):
    # it should return None if no column/value is missing
    mocker.patch("finance.validate.get_initial_balance", return_value=0)
    mocker.patch("finance.validate.get_pnl", return_value=0)
    mocker.patch("finance.validate.compare_balances", return_value=None)
    df = pd.DataFrame([range(5)], columns=v.COLS_BALANCE)
    mocker.patch("finance.validate.get_balances", return_value=df)
    mocker.patch("finance.dataframe.parse_csv", return_value=df)
    assert v.check_monthly_balances(DF, 2014) is None


def test_get_initial_balance(mocker):
    # it should return initial balance
    mocker.patch("finance.dataframe.parse_csv", return_value=DF_ACCOUNT)
    assert v.get_initial_balance(2013, "Cash", "HUF") == 1000
    assert v.get_initial_balance(2013, "Cash", "EUR") == 10
    assert v.get_initial_balance(2013, "Bank", "USD") == 345.3

    # it should throw error if multiple match found
    df_multiple = DF_ACCOUNT.append(DF_ACCOUNT)
    mocker.patch("finance.dataframe.parse_csv", return_value=df_multiple)
    with pytest.raises(ValueError) as context_info:
        v.get_initial_balance(2013, "Bank", "USD")
    assert "Multiple USD initial balance found for 'Bank'" in str(
        context_info.value
    )

    # throw error if no initial balance found for account
    with pytest.raises(ValueError) as context_info:
        v.get_initial_balance(2013, "Loan", "USD")
    assert "No 'Loan' found in column 'Account'" in str(context_info.value)

    # throw error if no initial balance found for account & currency
    with pytest.raises(ValueError) as context_info:
        v.get_initial_balance(2013, "Bank", "HUF")
    assert "No 'HUF' found in column 'Currency'" in str(context_info.value)

    # it should throw error if column is missing
    for col in v.COLS_ACCOUNT:
        df_missing = DF_ACCOUNT.copy()
        del df_missing[col]
        mocker.patch("finance.dataframe.parse_csv", return_value=df_missing)
        with pytest.raises(ValueError) as context_info:
            v.get_initial_balance(2013, "Bank", "USD")
        assert f"Column '{col}' not found" in str(context_info.value)


def test_get_pnl(mocker):
    acc = "Account"
    ccy = "Currency"
    cat = "Category"
    d = dt.date
    # it should throw error if column is missing
    for col in DF.columns:
        df_missing = DF.copy()
        del df_missing[col]
        with pytest.raises(ValueError) as context_info:
            v.get_pnl(df_missing, {col: "Bank", ccy: "USD"}, d.today(), True)
        assert f"Column '{col}' not found" in str(context_info.value)

    # it should return account pnl for given date
    assert v.get_pnl(DF, {acc: "Cash", ccy: "HUF"}, d(2012, 1, 12)) == 0
    assert v.get_pnl(DF, {acc: "Cash", ccy: "EUR"}, d(2012, 1, 12)) == 0
    assert v.get_pnl(DF, {acc: "Cash", ccy: "EUR"}, d(2012, 12, 12)) == 123.2
    assert v.get_pnl(DF, {acc: "Bank", ccy: "EUR"}, d(2012, 12, 12)) == 0
    assert v.get_pnl(DF, {acc: "Bank", ccy: "USD"}, d(2012, 10, 12)) == 0
    assert v.get_pnl(DF, {acc: "Bank", ccy: "USD"}, d(2012, 11, 12)) == -100

    # it should work without date
    assert v.get_pnl(DF, {acc: "Cash", ccy: "HUF"}) == 0
    assert v.get_pnl(DF, {acc: "Cash", ccy: "EUR"}) == 123.2
    assert v.get_pnl(DF, {acc: "Bank", ccy: "EUR"}) == 0
    assert v.get_pnl(DF, {acc: "Bank", ccy: "USD"}) == -100

    # throw error if account or currency is missing
    with pytest.raises(ValueError) as context_info:
        v.get_pnl(DF, {acc: "Loan", ccy: "USD"}, d.today(), raise_error=True)
    assert "No 'Loan' found in column 'Account'" in str(context_info.value)
    with pytest.raises(ValueError) as context_info:
        v.get_pnl(DF, {acc: "Bank", ccy: "HUF"}, d.today(), raise_error=True)
    assert "No 'HUF' found in column 'Currency'" in str(context_info.value)

    # it should work for category columns too
    assert v.get_pnl(DF, {cat: "Groceries", ccy: "HUF"}, d(2012, 1, 12)) == 0
    assert v.get_pnl(DF, {cat: "Groceries", ccy: "EUR"}, d(2012, 1, 12)) == 0
    assert (
        v.get_pnl(DF, {cat: "Groceries", ccy: "EUR"}, d(2012, 12, 12)) == 123.2
    )
    assert v.get_pnl(DF, {cat: "Transfer", ccy: "EUR"}, d(2012, 12, 12)) == 0
    assert v.get_pnl(DF, {cat: "Transfer", ccy: "USD"}, d(2012, 10, 12)) == 0
    assert (
        v.get_pnl(DF, {cat: "Transfer", ccy: "USD"}, d(2012, 11, 12)) == -100
    )


def test_compare_balances(mocker):
    # it should return None if balances match
    dt_bal = dt.date(2031, 12, 20)
    assert v.compare_balances(0, 100, 80, 20, "Bank", "USD", dt_bal) is None
    # it should throw error if balances don't match
    mocker.patch("finance.functions.balance_info", return_value=None)
    with pytest.raises(ValueError) as context_info:
        assert v.compare_balances(0, 100, 80, 10, "Bank", "USD", dt_bal)
    assert "Balance mismatch for Bank" in str(context_info.value)


FX_RATES = {"USD": 300, "EUR": 200, "HUF": 1}


def test_convert_amount():
    # it should return same amount if currencies are the same
    assert v.convert_amount(1, "HUF", "HUF", FX_RATES) == 1
    assert v.convert_amount(1, "USD", "USD", FX_RATES) == 1
    assert v.convert_amount(1, "EUR", "EUR", FX_RATES) == 1
    # it should handle missing currencies if they are the same
    assert v.convert_amount(1, "GBP", "GBP", FX_RATES) == 1
    # it should convert amount
    assert v.convert_amount(1, "USD", "HUF", FX_RATES) == 300
    assert v.convert_amount(1, "EUR", "HUF", FX_RATES) == 200
    assert v.convert_amount(3, "EUR", "USD", FX_RATES) == 2
    # it should throw error if currency is missing
    with pytest.raises(ValueError) as context_info:
        assert v.convert_amount(3, "GBP", "USD", FX_RATES)
    assert "No FX rate found for 'GBP'" in str(context_info.value)


def test_(tmp_path, mocker):
    f_path = tmp_path / "fx.json"
    f_path.write_text(json.dumps(FX_RATES))
    mocker.patch("finance.functions.get_path", return_value=f_path)
    assert v.get_fx_rates(2016) == FX_RATES
