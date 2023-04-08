#!/usr/bin/env python
import os

import finance.categorize as c
import finance.parser as p
import finance.report as r
import finance.validate as v
import finance.functions as f

year = 2023
r.get_balance(year)
# f.copy_cash_file(year)
df_cat = c.parse_categories_from_transactions(year)
df = p.parse_transactions(year)
df = c.match_existing_categories(df, df_cat, year)
v.check_monthly_balances(df, year)
df, df_sum = r.summarize_months(year, df)
r.save_results(df=df, df_sum=df_sum, f_path=f"./data/2023/output/summary.xlsx")
r.get_pnl(year, df)
