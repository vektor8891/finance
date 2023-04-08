#!/usr/bin/env python

import datetime as dt

import pandas as pd

import finance.dataframe as d
import finance.functions as f

COLS_BALANCE = ["Account", "Balance", "Currency", "Date", "Adjustment"]
COLS_ACCOUNT = ["Account", "Currency", "InitialBalance"]


def get_balances(year: int):
    df_balances = d.parse_csv(year, "settings", "balances.csv")
    d.has_columns(df_balances, COLS_BALANCE, raise_error=True)
    df_balances["Date"] = pd.to_datetime(df_balances["Date"]).dt.date
    df_balances = d.fill_column(df_balances, "Adjustment", 0)
    for col in COLS_BALANCE:
        d.has_missing_values(df_balances, col, raise_error=True)
    return df_balances


def check_monthly_balances(df: pd.DataFrame, year: int):
    df_balances = get_balances(year)

    # compare balances
    print("Check monthly balances:")
    for index, row in df_balances.iterrows():
        account = row["Account"]
        currency = row["Currency"]
        balance_date = row["Date"]
        balance_reported = row["Balance"]
        adjustment = row["Adjustment"]

        print(f"-- {balance_date}: {account}")
        balance_initial = get_initial_balance(year, account, currency)
        should_have_pnl = balance_initial != (adjustment + balance_reported)
        account_pnl = get_pnl(
            df,
            {"Account": account, "Currency": currency},
            balance_date,
            raise_error=should_have_pnl,
        )
        compare_balances(
            balance_initial,
            account_pnl,
            balance_reported,
            adjustment,
            account,
            currency,
            balance_date,
        )

    print("All balances are checked! :)")


def get_initial_balance(year: int, account: str, currency: str) -> float:
    df = d.parse_csv(year, "settings", "accounts.csv")
    d.has_columns(df, COLS_ACCOUNT, raise_error=True)
    df_filter = d.filter_values(
        df, {"Account": account, "Currency": currency}, raise_error=True
    )
    if len(df_filter.index) > 1:
        raise ValueError(
            f"Multiple {currency} initial balance found for "
            f"'{account}' ({year})"
        )
    return df_filter["InitialBalance"].values[0]


def get_pnl(
    df: pd.DataFrame,
    filter_dict: dict,
    cutoff_date=None,
    raise_error=False,
) -> float:
    d.has_column(df, "Amount", raise_error=True)
    df_pnl = d.filter_values(df, filter_dict, raise_error)
    if cutoff_date:
        d.has_column(df, "Date", raise_error=True)
        df_pnl = d.filter_date(df_pnl, cutoff_date)
    return df_pnl["Amount"].sum()


def compare_balances(
    balance_initial: float,
    account_pnl: float,
    balance_reported: float,
    adjustment: float,
    account: str,
    currency: str,
    balance_date: dt.date,
):
    balance_actual = account_pnl + balance_initial
    balance_expected = balance_reported + adjustment
    balance_diff = balance_expected - balance_actual
    if abs(balance_diff) > 0.01:
        print(
            f.balance_info(
                currency,
                balance_initial,
                account_pnl,
                balance_reported,
                adjustment,
            )
        )
        raise ValueError(f"Balance mismatch for {account} ({balance_date})")


def convert_amount(
    amount: float, ccy_from: str, ccy_to: str, fx_rates: dict
) -> float:
    if ccy_from == ccy_to:
        return amount
    else:

        def get_fx_rate(ccy: str):
            if ccy in fx_rates.keys():
                return fx_rates[ccy]
            else:
                raise ValueError(f"No FX rate found for '{ccy}'")

        return round(amount * get_fx_rate(ccy_from) / get_fx_rate(ccy_to), 2)


def get_fx_rates(year: int):
    f_path = f.get_path(year, "settings", "fx_rates.json")
    fx_rates = f.read_json(f_path)
    return fx_rates
