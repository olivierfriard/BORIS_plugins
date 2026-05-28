"""
BORIS plugin

Latency between behaviors
"""

import pandas as pd

__version__ = "0.1.3"
__version_date__ = "2026-04-13"
__plugin_name__ = "Behavior latency"
__author__ = "Olivier Friard - University of Torino - Italy"


GROUP_BY_COLUMNS = ["Observation id", "Subject"]
SORT_COLUMNS = ["Observation id", "Subject", "Start (s)", "Stop (s)", "Behavior"]


def run(df: pd.DataFrame) -> tuple[tuple[str, pd.DataFrame], tuple[str, pd.DataFrame]]:
    """
    Calculate latency between pairs of behaviors for each observation and subject.

    The latency is defined as:
    start time of behavior B - stop time of the latest previous behavior A

    Returns:
        A dataframe with one row for each detected A -> B transition.
        A summary dataframe grouped by subject and behavior pair.
    """

    required_columns = {"Observation id", "Subject", "Behavior", "Start (s)", "Stop (s)"}
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        return (("Behavior latency - Missing columns", pd.DataFrame({"missing column": missing_columns})),)

    if df.empty:
        empty = pd.DataFrame(
            columns=[
                "Observation id",
                "Subject",
                "Behavior A",
                "Behavior B",
                "A stop (s)",
                "B start (s)",
                "Latency (s)",
            ]
        )
        summary = pd.DataFrame(
            columns=[
                "Behavior A",
                "Behavior B",
                "Subject",
                "count",
                "latency mean (s)",
                "latency median (s)",
                "latency min (s)",
                "latency max (s)",
                "latency std dev (s)",
            ]
        )
        return ("Behavior latency - Detail", empty), ("Behavior latency - Summary by subject", summary)

    df_sorted = df.loc[:, list(required_columns)].copy()
    df_sorted = df_sorted.dropna(subset=["Observation id", "Subject", "Behavior", "Start (s)", "Stop (s)"])
    df_sorted = df_sorted.sort_values(by=SORT_COLUMNS, kind="stable")

    latency_rows: list[dict] = []

    for (observation_id, subject), group in df_sorted.groupby(GROUP_BY_COLUMNS, dropna=False, sort=False):
        last_event_by_behavior: dict[str, dict] = {}

        for current_event in group.to_dict("records"):
            current_behavior = current_event["Behavior"]

            for previous_behavior, previous_event in last_event_by_behavior.items():
                if previous_behavior == current_behavior:
                    continue

                latency = float(current_event["Start (s)"] - previous_event["Stop (s)"])
                latency_rows.append(
                    {
                        "Observation id": observation_id,
                        "Subject": subject,
                        "Behavior A": previous_behavior,
                        "Behavior B": current_behavior,
                        "A stop (s)": float(previous_event["Stop (s)"]),
                        "B start (s)": float(current_event["Start (s)"]),
                        "Latency (s)": round(latency, 3),
                    }
                )

            last_event_by_behavior[current_behavior] = current_event

    latency_df = pd.DataFrame(latency_rows)

    if latency_df.empty:
        summary = pd.DataFrame(
            columns=[
                "Behavior A",
                "Behavior B",
                "Subject",
                "count",
                "latency mean (s)",
                "latency median (s)",
                "latency min (s)",
                "latency max (s)",
                "latency std dev (s)",
            ]
        )
        return ("Behavior latency - Detail", latency_df), ("Behavior latency - Summary by subject", summary)

    summary_df = (
        latency_df.groupby(["Subject", "Behavior A", "Behavior B"])["Latency (s)"]
        .agg(["count", "mean", "median", "min", "max", "std"])
        .reset_index()
        .rename(
            columns={
                "mean": "latency mean (s)",
                "median": "latency median (s)",
                "min": "latency min (s)",
                "max": "latency max (s)",
                "std": "latency std dev (s)",
            }
        )
        .round(3)
        .sort_values(by=["Subject", "Behavior A", "Behavior B"], kind="stable")
    )

    latency_df = latency_df.sort_values(by=["Observation id", "Subject", "Behavior A", "Behavior B", "B start (s)"], kind="stable")

    return ("Behavior latency - Detail", latency_df), ("Behavior latency - Summary by subject", summary_df)
