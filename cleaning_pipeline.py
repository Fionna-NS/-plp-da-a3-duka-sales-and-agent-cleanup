import pandas as pd



def clean_agent_data(txns, agents):
    """Clean the raw agent transaction extract and merge it with the agent register.

    Parameters
    ----------
    txns : pd.DataFrame  raw transactions (txn_id, agent_id, txn_type, amount, txn_date)
    agents : pd.DataFrame  agent register (agent_id, county, onboarded)

    Returns
    -------
    clean_df : pd.DataFrame  cleaned transactions with county, amount_imputed, is_outlier
    log : pd.DataFrame  one row per cleaning rule: rule, dimension, column, rows_affected, action
    """
    df = txns.copy()
    log = []

    def record(rule, dimension, column, rows, action):
        log.append({"rule": rule, "dimension": dimension, "column": column,
                    "rows_affected": int(rows), "action": action})

    # 1. Uniqueness: duplicate txn_id
    dup = df.duplicated(subset="txn_id", keep="first")
    record("duplicate txn_id", "Uniqueness", "txn_id", dup.sum(), "removed, kept first")
    df = df[~dup].copy()

    # 2. Consistency: txn_type -> exactly Deposit / Withdrawal
    mapped = df["txn_type"].str.strip().str.lower().map(
        {"deposit": "Deposit", "withdrawal": "Withdrawal"})
    record("non-standard txn_type", "Consistency", "txn_type",
           (df["txn_type"] != mapped).sum(), "stripped, case-normalised")
    assert mapped.notna().all(), "unexpected txn_type value"
    df["txn_type"] = mapped

    # 3. Validity/type: txn_date with mixed separators -> datetime
    raw_date = df["txn_date"].astype(str)
    record("slash-formatted dates", "Consistency", "txn_date",
           raw_date.str.contains("/").sum(), "replaced / with -, parsed as ISO")
    df["txn_date"] = pd.to_datetime(raw_date.str.replace("/", "-"),
                                    format="%Y-%m-%d", errors="coerce")

    # 4. Validity/type: amount -> numeric (blank and "N/A" become NaN)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    missing = df["amount"].isna()
    record("missing/invalid amount", "Completeness", "amount", missing.sum(),
           "flagged, imputed (step 6)")

    # 5. Accuracy: IQR outlier flag (on valid amounts only)
    q1, q3 = df["amount"].quantile([0.25, 0.75])
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    df["is_outlier"] = (df["amount"] < lo) | (df["amount"] > hi)   # NaN -> False
    record("IQR outlier", "Accuracy", "amount", df["is_outlier"].sum(),
           "flagged, not removed")

    # 6. Completeness: impute with the median per txn_type (non-outliers), flag it
    med = df.loc[~df["is_outlier"]].groupby("txn_type")["amount"].median()
    df["amount_imputed"] = missing
    df["amount"] = df["amount"].fillna(df["txn_type"].map(med))

    # 7. Merge: LEFT join so unknown agents are kept and counted
    out = df.merge(agents[["agent_id", "county"]], on="agent_id",
                   how="left", validate="m:1", indicator=True)
    unknown = out["_merge"] == "left_only"
    record("unknown agent_id", "Validity", "agent_id", unknown.sum(),
           "kept, county set to 'Unknown'")
    out["county"] = out["county"].fillna("Unknown")
    return out.drop(columns="_merge"), pd.DataFrame(log)
