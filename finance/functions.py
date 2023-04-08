#!/usr/bin/env python

import json
import os
import os.path as p


def get_path(year: int, folder_name: str, file_name=None):
    folder_path = p.join("data", str(year), folder_name)
    return p.join(folder_path, file_name) if file_name else folder_path


def get_transaction_files(year: int):
    folder_path = get_path(year, "input")
    files = os.listdir(folder_path)
    return files


def balance_info(currency: str, balance_initial: float, account_pnl: float, balance_reported: float,
                 adjustment: float, ):
    balance_actual = balance_initial + account_pnl
    bal_expected = balance_reported + adjustment
    balance_diff = bal_expected - balance_actual
    new_adjustment = "{:.2f}".format(adjustment - balance_diff)
    bal_info = (f"\tA) Initial:\t\t\t\t{print_number(balance_initial)} {currency}\n"
                f"\tB) PnL:\t\t\t\t\t{print_number(account_pnl)} {currency}\n"
                f"\tC) ACTUAL (A+B):\t\t{print_number(balance_actual)} {currency}\n"
                f"\tD) Reported:\t\t\t{print_number(balance_reported)} {currency}\n"
                f"\tE) Adjustment:\t\t\t{print_number(adjustment)} {currency}\n"
                f"\tF) EXPECTED (D+E):\t\t{print_number(bal_expected)} {currency}\n"
                f"\tG) DIFFERENCE (F-C):\t{print_number(balance_diff)} {currency}\n"
                f"\t--------------------------------------------\n"
                f"\tHINT: Set E) to {new_adjustment} to resolve difference")
    return bal_info


def print_number(number: float):
    number_string = "{:10.2f}".format(number)
    return number_string


def read_json(f_path: str):
    with open(f_path, "r") as f:
        data = json.load(f)
    return data


def copy_cash_file(year):
    import shutil
    import os

    old_file = f"/home/vszabo/Dropbox/Backup_personal/Cash_{year}.txt"
    destination = get_path(year, "input", "Cash.csv")

    if os.path.isfile(old_file):
        shutil.copy(old_file, destination)
