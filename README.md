# Duka Sales Exploration and Agent Data Cleanup

Two client engagements from a Nairobi analytics consultancy, both done in Python (pandas, numpy) with one spreadsheet task.

## Engagement 1: Duka Electronics (sales exploration)

Duka Electronics' Head of Sales asked for answers ahead of the half-year review. The data is 1,000 orders from January to June 2026 (seed 2026). Notebook: `duka_sales_exploration.ipynb`.

Key findings:
- Total revenue is KES 71,792,500. Nairobi leads with KES 26.1M (36.4%), followed by Mombasa, Nakuru, Kisumu and Eldoret. The ranking is identical by revenue and by number of orders, because order volume differs far more between branches than average order value does.
- By revenue the top products are Laptop (KES 41.5M), Tablet (KES 19.3M) and Phone (KES 8.9M). By units they are Tablet (691), Laptop (639) and Phone (592). Laptop and Tablet swap places because of price.
- Weekends account for 277 orders (27.7%) and KES 19.9M, in line with their 28.9% share of calendar days. Average order revenue is almost identical (KES 71,972 vs 71,724).
- April is the best month (KES 13.52M) and June the worst (KES 10.90M), a gap of 24.0%. June only has data up to 29 June.
- There are 83 Premium online orders from Nairobi and Mombasa, worth KES 10,218,000 (14.2% of revenue). They are saved in `outputs/premium_online_coast_capital.csv`.
- Spreadsheet task: `excel/duka_branch_summary.xlsx` holds a SUMIFS branch table, an XLOOKUP region column and a PivotTable of revenue by branch and channel. The notebook confirms that the Excel totals match pandas exactly (grand total KES 71,792,500).

Assumptions: `price_band` is based on `unit_price` (Premium ≥ KES 28,000, so Laptop and Tablet are Premium). Regions in the Excel file were assigned by the analyst and are not in the source data. XLOOKUP needs Excel 2021 or Microsoft 365.

### Duka Executive Summary

(Paste the final Executive Summary exactly as it appears in the notebook.)

## Engagement 2: Mobile money agent network (data cleaning)

The transaction extract from a legacy system was audited, cleaned, merged with the agent register and summarised. The data is 600 transactions from 20 agents (seed 44), plus injected problems. Notebook: `agent_cleanup.ipynb`. Cleaning code: `cleaning_pipeline.py`, function `clean_agent_data(txns, agents)`, which returns `(clean_df, log)`.

**Row counts: 612 rows before cleaning, 600 rows after.** The 12 removed rows were duplicate `txn_id` values. The left join to the agent register keeps all 600 rows.

| Issue (dimension) | Treatment |
|---|---|
| 12 duplicate transactions (Uniqueness) | Removed, keeping the first occurrence |
| 384 raw rows with inconsistent `txn_type` spelling, case or trailing spaces (Consistency) | Standardised to `Deposit` and `Withdrawal` |
| 5 dates written with `/` (Consistency) | Converted to ISO dates (`YYYY-MM-DD`) |
| 22 missing amounts in the raw file: 15 blank and 7 "N/A"; 20 remain after de-duplication (Completeness) | Imputed with the median amount per `txn_type`, flagged in `amount_imputed` |
| 40 IQR outliers, including 5 amounts of exactly 250,000 (Accuracy) | Flagged in `is_outlier`, not removed; the 250,000 values are one per county and about 47% of total value, so they are suspected system defaults to be verified with the source system |
| 7 transactions from agent `AG099`, not in the register (Validity) | Kept, with county set to "Unknown" |

No agent transacted before being onboarded, and transaction dates run from 1 March to 29 April 2026 (Timeliness). The notebook ends with a Data Quality Report organised by the six dimensions, including a privacy paragraph under the Kenya Data Protection Act 2019.

## Repository structure

```
README.md
generate_data.py                  both dataset generators (seed 2026 and seed 44), unchanged
duka_sales_exploration.ipynb      Engagement 1
cleaning_pipeline.py              clean_agent_data(txns, agents)
agent_cleanup.ipynb               Engagement 2
requirements.txt
excel/duka_branch_summary.xlsx
outputs/premium_online_coast_capital.csv
outputs/agent_transactions_clean.csv
```

The raw CSVs (`duka_sales.csv`, `agents.csv`, `agent_transactions.csv`) are not committed. They are regenerated from `generate_data.py`.

## How to regenerate the data and run the notebooks

1. Install the requirements: `pip install -r requirements.txt`
2. Generate the raw data: `python generate_data.py`. This creates `duka_sales.csv`, `agents.csv` and `agent_transactions.csv`.
3. Run `duka_sales_exploration.ipynb` from top to bottom. It reads `duka_sales.csv`, writes `outputs/premium_online_coast_capital.csv` and compares its totals with `excel/duka_branch_summary.xlsx`.
4. Run `agent_cleanup.ipynb` from top to bottom. It imports `clean_agent_data` from `cleaning_pipeline.py`, reads `agents.csv` and `agent_transactions.csv`, and writes `outputs/agent_transactions_clean.csv`.

Run both notebooks from the repository root, so the relative paths (`outputs/`, `excel/`) resolve.
