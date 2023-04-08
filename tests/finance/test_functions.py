#!/usr/bin/env python

import json
import os.path as p

import finance.functions as f

DICT_DATA = {"key": "value"}


def test_get_path():
    # it should create file/directory paths
    tests = [
        (1984, "empty_folder"),
        (1945, "folder", "file1.csv"),
        (1956, "folder", "file2.xlsx"),
        (1988, "folder", "file3.txt"),
    ]
    for t in tests:
        assert f.get_path(*t) == p.join("data", *tuple([str(v) for v in t]))


def test_get_transaction_files(tmp_path, mocker):
    files = ["test1.csv", "test2.xls", "test3.xlsx"]
    for file in files:
        f_path = tmp_path / file
        f_path.write_text("hello")
    mocker.patch("finance.functions.get_path", return_value=tmp_path)
    assert f.get_transaction_files(2001).sort() == files.sort()


def test_balance_info():
    balance_info = f.balance_info(
        currency="HUF",
        balance_reported=0,
        balance_initial=1,
        account_pnl=2,
        adjustment=3,
    )
    assert (
        balance_info == "\tA) Initial:\t\t\t\t      1.00 HUF\n"
        "\tB) PnL:\t\t\t\t\t      2.00 HUF\n"
        "\tC) ACTUAL (A+B):\t\t      3.00 HUF\n"
        "\tD) Reported:\t\t\t      0.00 HUF\n"
        "\tE) Adjustment:\t\t\t      3.00 HUF\n"
        "\tF) EXPECTED (D+E):\t\t      3.00 HUF\n"
        "\tG) DIFFERENCE (F-C):\t      0.00 HUF\n"
        "\t--------------------------------------------\n"
        "\tHINT: Set E) to 3.00 to resolve difference"
    )


def test_print_number():
    assert f.print_number(3.249) == "      3.25"


def test_read_json(tmp_path):
    data = {"key": "Value"}
    f_path = tmp_path / "test.json"
    f_path.write_text(json.dumps(data))
    assert f.read_json(f_path) == data
