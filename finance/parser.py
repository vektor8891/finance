#!/usr/bin/env python

import pandas as pd

import finance.dataframe as d
import finance.functions as f


class Parser:

    col_names = ["Date", "Account", "Amount", "Currency", "Details"]

    def __init__(
        self,
        year: int,
        file_name: str,
        currency="USD",
    ):

        self.year = year
        self.file_name = file_name
        self.account_name = file_name.split(".")[0]
        self.currency = currency

    def get_path(self):
        return f.get_path(self.year, "input", self.file_name)

    def read(self) -> pd.DataFrame:
        f_path = self.get_path()
        ext = f_path.split(".")[-1]
        # print(f_path)
        df = (
            pd.read_csv(f_path, encoding="utf-8", thousands=",")
            if ext == "csv"
            else pd.read_excel(f_path, thousands=",")
        )
        df = d.strip_col_names(df)
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = d.add_column(df, "Account", self.account_name)
        if not d.has_column(df, "Currency"):
            df = d.add_column(df, "Currency", self.currency)
        df = d.format_date(df, "Date", "%Y-%m-%d")
        df = d.filter_columns(df, col_list=Parser.col_names)
        df = d.merge_columns(
            df,
            column="Details",
            col_list=["Date", "Details"],
        )
        df = d.replace_value(df, "Details", "\\s{2,}", " ", regex=True)
        return df

    def validate(self, df: pd.DataFrame):
        # is not empty
        if len(df.index) == 0:
            raise ValueError("Empty dataframe!")
        # has mandatory column
        d.has_columns(df, Parser.col_names, raise_error=True)
        # has no extra column
        if len(df.columns) > len(Parser.col_names):
            raise ValueError("Extra columns found in dataframe!")
        # has no missing values
        for col in df.columns:
            d.has_missing_values(df, col, raise_error=True)
        # contains data for current year only
        years = list(set(pd.DatetimeIndex(df["Date"]).year))
        for year in years:
            if year != self.year:
                raise ValueError(f"Invalid year {year} found in data!")

    def parse(self):
        df = self.read()
        df = self.transform(df)
        self.validate(df)
        return df

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        else:
            is_equal = (
                self.year == other.year
                and self.file_name == other.file_name
                and self.account_name == other.account_name
                and self.currency == other.currency
            )
            return is_equal


class UnicreditParser(Parser):
    def __init__(self, year: int, file_name: str):
        super(UnicreditParser, self).__init__(year, file_name, currency="HUF")

    def transform(self, df) -> pd.DataFrame:
        # exclude rejected transactions
        df = d.filter_value(df, column="Státusz", value="Könyvelt")
        # convert Amount
        df = d.match_pattern(
            df,
            new_column="Amount",
            pattern_column="Összeg",
            pattern="[" "\\d|,|-]",
        )
        df = d.replace_value(df, column="Amount", value_from=",", value_to=".")
        df = d.convert_type(df, column="Amount", col_type="float")
        # convert Date
        df = d.rename_column(df, column_old="Érték Dátum", column_new="Date")
        df = d.format_date(df, column="Date", date_format="%Y.%m.%d")
        # get transaction Details
        df = d.merge_columns(
            df,
            column="Details",
            col_list=[
                "Partner",
                "Partner " "Számlaszám",
                "Tranzakció részletek",
            ],
        )
        # default data transforms
        df = super(UnicreditParser, self).transform(df)
        return df


class CapitalOneParser(Parser):
    def transform(self, df) -> pd.DataFrame:
        # convert Amount
        cols = ["Debit", "Credit"]
        df = d.fill_columns(df, cols, 0)
        df = d.multiple_column(df, column="Debit", multiplier=-1)
        df = d.summarize_columns(df, column="Amount", col_list=cols)
        # convert Date
        df = d.rename_column(df, column_old="Posted Date", column_new="Date")
        df = d.format_date(df, column="Date", date_format="%Y-%m-%d")
        # get transaction Details
        df = d.rename_column(
            df, column_old="Description", column_new="Details"
        )
        # default data transforms
        df = super(CapitalOneParser, self).transform(df)
        return df


class CapitalOneSavingsParser(Parser):
    def transform(self, df) -> pd.DataFrame:
        # convert Amount
        df = d.rename_column(df, column_old="Transaction Amount", column_new="Amount")
        # convert Date
        df = d.rename_column(df, column_old="Transaction Date", column_new="Date")
        df = d.format_date(df, column="Date", date_format="%m/%d/%y")
        # get transaction Details
        df = d.rename_column(
            df, column_old="Transaction Description", column_new="Details"
        )
        # default data transforms
        df = super(CapitalOneSavingsParser, self).transform(df)
        return df


class HSBCParser(Parser):
    def transform(self, df) -> pd.DataFrame:
        # convert Date
        df = d.format_date(df, column="Date", date_format="%m/%d/%Y")
        # default data transforms
        df = super(HSBCParser, self).transform(df)
        return df


class HSBCMasterCardParser(HSBCParser):
    def transform(self, df) -> pd.DataFrame:
        # convert Amount
        df = d.replace_value(df, "Amount", value_from="--", value_to="-")
        df = d.replace_value(df, "Amount", value_from=",", value_to="")
        df = d.convert_type(df, column="Amount", col_type="float")
        df = d.multiple_column(df, column="Amount", multiplier=-1)
        df = super(HSBCMasterCardParser, self).transform(df)
        return df


class WiseParser(Parser):
    def transform(self, df) -> pd.DataFrame:
        # get transaction Details
        df = d.merge_columns(
            df,
            column="Details",
            col_list=[
                "Description",
                "Payment Reference",
                "Payee Name",
                "Payee Account Number",
            ],
        )
        # convert Date
        df = d.format_date(df, column="Date", date_format="%d-%m-%Y")
        # default data transforms
        df = super(WiseParser, self).transform(df)
        return df


def get_parser_object(year: int, file_name: str) -> Parser:

    if file_name.startswith("Unicredit"):
        return UnicreditParser(year, file_name)
    elif file_name.startswith("Cash"):
        return Parser(year, file_name)
    elif file_name.startswith("CapitalOne_Savings"):
        return CapitalOneSavingsParser(year, file_name)
    elif file_name.startswith("CapitalOne"):
        return CapitalOneParser(year, file_name)
    elif file_name.startswith("HSBC_Mastercard"):
        return HSBCMasterCardParser(year, file_name)
    elif file_name.startswith("HSBC"):
        return HSBCParser(year, file_name)
    elif file_name.startswith("Wise"):
        return WiseParser(year, file_name)
    else:
        raise ValueError(f'Cannot find parser object for "{file_name}"')


def parse_transaction_file(year: int, file_name: str) -> pd.DataFrame:
    parser_obj = get_parser_object(year, file_name)
    df = parser_obj.parse()
    return df


def parse_transactions(year: int) -> pd.DataFrame:
    df_all = pd.DataFrame()
    transaction_files = f.get_transaction_files(year)
    print("Parse transactions:")
    for transaction_file in transaction_files:
        print(f"-- {transaction_file}")
        if not transaction_file.startswith(".~lock"):
            df_new = parse_transaction_file(year, transaction_file)
            df_all = (
                df_new
                if df_all.empty
                else pd.concat([df_all, df_new])
            )
    return df_all
