#!/usr/bin/env python

import datetime as dt

import numpy as np
import pandas as pd
import pytest

import finance.report as rpt

DF = pd.DataFrame(
    data={
        "Category": ["Groceries", "Restaurant"],
        "Currency": ["HUF", "USD"],
        "Amount": [900, 10],
        "Date": [dt.date(2019, 3, 10), dt.date(2019, 2, 20)],
    }
)

DF_CAT = pd.DataFrame(
    data={
        "Type": ["Income", "Income"],
        "Group": ["Food", "Food"],
        "Category": ["Groceries", "Restaurant"],
    }
)

DF_ACC = pd.DataFrame(
    data={
        "Account": ["Bank", "Bank", "Bank"],
        "Amount": [100, 400, -200],
        "Currency": ["USD", "USD", "USD"],
        "Date": [
            dt.date(2019, 3, 12),
            dt.date(2019, 6, 19),
            dt.date(2019, 6, 19),
        ],
    }
)


def test_add_usd_amount(mocker):

    # it should throw errors if columns are missing
    with pytest.raises(ValueError) as context_info:
        rpt.add_usd_amount(2019, pd.DataFrame(columns=["Currency"]))
    assert "Column 'Amount' not found" in str(context_info.value)
    with pytest.raises(ValueError) as context_info:
        rpt.add_usd_amount(2019, pd.DataFrame(columns=["Amount"]))
    assert "Column 'Currency' not found" in str(context_info.value)

    # it should convert amount to USD
    df = pd.DataFrame(data={"Currency": ["HUF"], "Amount": [300]})
    df_expected = df.copy()
    df_expected["AmountUSD"] = 1.0
    mocker.patch(
        "finance.validate.get_fx_rates", return_value={"USD": 300, "HUF": 1}
    )
    assert rpt.add_usd_amount(2019, df).equals(df_expected)


def test_summarize_transactions(mocker, tmp_path):
    # it should throw error if column is missing
    with pytest.raises(ValueError) as context_info:
        rpt.summarize_transactions(pd.DataFrame())
    assert "Column 'Date' not found" in str(context_info.value)

    # it should summarize transactions
    df = pd.DataFrame(
        data={"Date": [dt.date(2019, 3, 10), dt.date(2019, 2, 20)]}
    )
    df_expected = pd.DataFrame(
        data={
            "Date": [dt.date(2019, 2, 20), dt.date(2019, 3, 10)],
            "Month": [2, 3],
        }
    )
    assert rpt.summarize_transactions(df).equals(df_expected)


def test_summarize_categories(mocker, tmp_path):
    def get_transaction(
        cat_type="Type", category="Cat1", month=1, amount=100
    ):
        return pd.DataFrame(
            data={
                "CategoryType": [cat_type],
                "CategoryName": [category],
                "Month": [month],
                "AmountUSD": [amount],
            }
        )

    # it should throw error if any column is missing
    df = get_transaction()
    for col in df.columns:
        df_missing = df.copy()
        del df_missing[col]
        with pytest.raises(ValueError) as context_info:
            rpt.summarize_categories(df_missing)
        assert f"Column '{col}' not found" in str(context_info.value)
        if col != "Category":
            with pytest.raises(ValueError) as context_info:
                rpt.summarize_categories(df_missing)
            assert f"Column '{col}' not found" in str(context_info.value)

    # it should summarize transactions per category
    df_multi = pd.concat(
        [
            get_transaction(),
            get_transaction(month=2),
            get_transaction(month=2),
            get_transaction(category="Cat2", amount=50),
            get_transaction(category="Cat2", month=2),
            get_transaction(category="Cat2", month=2),
            get_transaction(category="Cat2", month=2),
        ]
    )
    df_cat_expected = pd.DataFrame(
        data={
            "CategoryType": ["Type", "Type"],
            "CategoryName": ["Cat1", "Cat2"],
            1: [100, 50],
            2: [200, 300],
        }
    )
    assert rpt.summarize_categories(df_multi).equals(
        df_cat_expected
    )


def test_summarize_months(mocker):
    mocker.patch("finance.report.add_usd_amount", return_value=DF)
    mocker.patch("finance.report.summarize_transactions", return_value=DF)
    mocker.patch("finance.report.summarize_categories", return_value=DF)
    assert rpt.summarize_months(2019, DF)[0].equals(DF)
    assert rpt.summarize_months(2019, DF)[1].equals(DF)
