"""
BORIS plugin

Behavior by frame
"""

import math

import pandas as pd

__version__ = "0.1.0"
__version_date__ = "2026-06-26"
__plugin_name__ = "Behavior by frame"
__author__ = "Olivier Friard - University of Torino - Italy"
__description__ = "Generate a frame-by-frame table showing the active behavior labels for each subject in media observations."


FPS_COLUMNS = ("FPS (frame/s)", "FPS", "fps")
MEDIA_DURATION_COLUMNS = ("Media duration (s)",)
FRAME_COUNT_COLUMNS = ("Frame count", "Frames number", "Number of frames")
REQUIRED_COLUMNS = {"Observation id", "Subject", "Behavior", "Start (s)", "Stop (s)"}
OUTPUT_COLUMNS = [
    "Observation id",
    "Subject",
    "Frame index",
    "Time (s)",
    "Behavior",
]
BEHAVIOR_SEPARATOR = " + "
MODIFIER_SEPARATOR = "|"
MODIFIER_VALUE_SEPARATOR = ","
MEDIA_OBSERVATION_TYPE = "MEDIA"
POINT_EVENT_TYPE = "Point event"
TIME_FULL_OBS = "full obs"
TIME_EVENTS = "limit to events"
TIME_ARBITRARY_INTERVAL = "time interval"
EPSILON = 1e-9


def run(df: pd.DataFrame, parameters: dict = None) -> pd.DataFrame | tuple[str, pd.DataFrame]:
    """
    Return the current behavior labels for each video frame.
    """

    fps_column = dataframe_fps_column(df)
    required_columns = set(REQUIRED_COLUMNS)
    if fps_column is None:
        required_columns.add(FPS_COLUMNS[0])

    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        return "Behavior by frame - Missing columns", pd.DataFrame({"missing column": missing_columns})

    df = selected_rows(df, parameters).copy()
    if "Observation type" in df.columns:
        df = df[df["Observation type"].astype(str).str.upper() == MEDIA_OBSERVATION_TYPE]
    df = df.sort_values(by=["Observation id"], key=lambda column: column.astype(str), kind="stable")

    include_modifiers = bool(parameters.get("include modifiers", False)) if parameters else False
    modifier_columns = behavior_modifier_columns(df) if include_modifiers else []

    output_columns = list(OUTPUT_COLUMNS)
    if "Media file name" in df.columns:
        output_columns.insert(2, "Media file name")

    if df.empty:
        return pd.DataFrame(columns=output_columns)

    rows: list[dict] = []
    group_columns = ["Observation id", "Subject"]
    if "Media file name" in df.columns:
        group_columns.insert(1, "Media file name")

    for group_values, group in df.groupby(group_columns, dropna=False, sort=False):
        if not isinstance(group_values, tuple):
            group_values = (group_values,)
        group_info = dict(zip(group_columns, group_values))

        fps = first_positive_number(group[fps_column])
        if fps is None:
            continue

        start_frame, stop_frame = frame_range(group, fps, parameters)
        if stop_frame <= start_frame:
            continue

        event_records = sorted_event_records(group, modifier_columns)
        point_events_by_frame = point_events_by_frame_index(event_records, fps)

        for frame_index in range(start_frame, stop_frame):
            frame_time = frame_index / fps
            labels = current_labels(event_records, point_events_by_frame, frame_index, frame_time)
            row = {
                "Observation id": group_info["Observation id"],
                "Subject": group_info["Subject"],
                "Frame index": frame_index,
                "Time (s)": round(frame_time, 6),
                "Behavior": BEHAVIOR_SEPARATOR.join(labels),
            }
            if "Media file name" in group_info:
                row["Media file name"] = group_info["Media file name"]
            rows.append(row)

    return pd.DataFrame(rows, columns=output_columns)


def dataframe_fps_column(df: pd.DataFrame) -> str | None:
    for column in FPS_COLUMNS:
        if column in df.columns:
            return column
    return None


def selected_rows(df: pd.DataFrame, parameters: dict = None) -> pd.DataFrame:
    """
    Keep only selected subjects and behaviors when parameters are provided.
    """

    if not parameters:
        return df

    if "Observation id" in df.columns and parameters.get("selected observations"):
        df = df[df["Observation id"].isin(parameters["selected observations"])]

    if "Subject" in df.columns and parameters.get("selected subjects"):
        df = df[df["Subject"].isin(parameters["selected subjects"])]

    if "Behavior" in df.columns and parameters.get("selected behaviors"):
        df = df[df["Behavior"].isin(parameters["selected behaviors"])]

    return df


def behavior_modifier_columns(df: pd.DataFrame) -> list[tuple]:
    """
    Return BORIS modifier columns named as (behavior code, modifier set).
    """

    return [column for column in df.columns if isinstance(column, tuple) and len(column) >= 2]


def sorted_event_records(group: pd.DataFrame, modifier_columns: list[tuple]) -> list[dict]:
    df_events = group.dropna(subset=["Behavior", "Start (s)", "Stop (s)"]).copy()
    if df_events.empty:
        return []

    df_events["Start (s)"] = pd.to_numeric(df_events["Start (s)"], errors="coerce")
    df_events["Stop (s)"] = pd.to_numeric(df_events["Stop (s)"], errors="coerce")
    df_events = df_events.dropna(subset=["Start (s)", "Stop (s)"])
    df_events = df_events.sort_values(by=["Start (s)", "Stop (s)", "Behavior"], kind="stable")

    records: list[dict] = []
    for row in df_events.to_dict("records"):
        records.append(
            {
                "start": float(row["Start (s)"]),
                "stop": float(row["Stop (s)"]),
                "is_point": is_point_event(row),
                "label": behavior_label(row, modifier_columns),
            }
        )
    return records


def is_point_event(row: dict) -> bool:
    if str(row.get("Behavior type", "")).startswith(POINT_EVENT_TYPE):
        return True
    return abs(float(row["Stop (s)"]) - float(row["Start (s)"])) <= EPSILON


def behavior_label(row: dict, modifier_columns: list[tuple]) -> str:
    behavior = row["Behavior"]
    label = str(behavior)
    modifiers = row_modifier_values(row, behavior, modifier_columns)
    if modifiers:
        label += MODIFIER_SEPARATOR + MODIFIER_VALUE_SEPARATOR.join(modifiers)
    return label


def row_modifier_values(row: dict, behavior: object, modifier_columns: list[tuple]) -> list[str]:
    modifiers: list[str] = []

    for column in modifier_columns:
        if column[0] != behavior:
            continue
        modifiers.extend(label_value_strings(row.get(column)))

    return modifiers


def label_value_strings(value: object) -> list[str]:
    if isinstance(value, (list, tuple)):
        values = value
    else:
        values = [value]

    strings: list[str] = []
    for item in values:
        try:
            if pd.isna(item):
                continue
        except (TypeError, ValueError):
            pass
        text = str(item).strip()
        if text:
            strings.append(text)

    return strings


def point_events_by_frame_index(event_records: list[dict], fps: float) -> dict[int, list[str]]:
    point_events: dict[int, list[str]] = {}
    for event in event_records:
        if not event["is_point"]:
            continue
        frame_index = int(math.floor(event["start"] * fps + EPSILON))
        point_events.setdefault(frame_index, []).append(event["label"])
    return point_events


def current_labels(
    event_records: list[dict],
    point_events_by_frame: dict[int, list[str]],
    frame_index: int,
    frame_time: float,
) -> list[str]:
    labels: list[str] = []
    seen_labels: set[str] = set()

    for event in event_records:
        if event["is_point"]:
            continue
        if event["start"] <= frame_time + EPSILON and frame_time < event["stop"] - EPSILON:
            add_label(labels, seen_labels, event["label"])

    for label in point_events_by_frame.get(frame_index, []):
        add_label(labels, seen_labels, label)

    return labels


def add_label(labels: list[str], seen_labels: set[str], label: str) -> None:
    if label in seen_labels:
        return
    labels.append(label)
    seen_labels.add(label)


def frame_range(group: pd.DataFrame, fps: float, parameters: dict = None) -> tuple[int, int]:
    time_mode = parameters.get("time") if parameters else None

    if time_mode == TIME_EVENTS:
        return observed_events_frame_range(group, fps)

    if time_mode == TIME_ARBITRARY_INTERVAL:
        selected_start, selected_stop = selected_time_bounds(parameters)
        return time_bounds_frame_range(selected_start, selected_stop, fps)

    if time_mode == TIME_FULL_OBS:
        return media_duration_frame_range(group, fps)

    selected_start, selected_stop = selected_time_bounds(parameters)
    if selected_start is not None or selected_stop is not None:
        return time_bounds_frame_range(selected_start, selected_stop, fps)

    return media_duration_frame_range(group, fps)


def observed_events_frame_range(group: pd.DataFrame, fps: float) -> tuple[int, int]:
    df_events = group.dropna(subset=["Start (s)", "Stop (s)"]).copy()
    if df_events.empty:
        return 0, 0

    df_events["Start (s)"] = pd.to_numeric(df_events["Start (s)"], errors="coerce")
    df_events["Stop (s)"] = pd.to_numeric(df_events["Stop (s)"], errors="coerce")
    df_events = df_events.dropna(subset=["Start (s)", "Stop (s)"])
    if df_events.empty:
        return 0, 0

    start_frames: list[int] = []
    stop_frames: list[int] = []

    for row in df_events.to_dict("records"):
        start_time = max(0.0, float(row["Start (s)"]))
        stop_time = max(start_time, float(row["Stop (s)"]))
        if is_point_event(row):
            frame_index = int(math.floor(start_time * fps + EPSILON))
            start_frames.append(frame_index)
            stop_frames.append(frame_index + 1)
        else:
            start_frames.append(int(math.ceil(start_time * fps - EPSILON)))
            stop_frames.append(int(math.ceil(stop_time * fps - EPSILON)))

    if not start_frames or not stop_frames:
        return 0, 0

    return min(start_frames), max(stop_frames)


def time_bounds_frame_range(start_time: float | None, stop_time: float | None, fps: float) -> tuple[int, int]:
    start_time = max(0.0, start_time or 0.0)
    if stop_time is None:
        return int(math.ceil(start_time * fps - EPSILON)), int(math.ceil(start_time * fps - EPSILON))

    stop_time = max(float(stop_time), start_time)
    start_frame = int(math.ceil(start_time * fps - EPSILON))
    stop_frame = int(math.ceil(stop_time * fps - EPSILON))
    return max(0, start_frame), max(0, stop_frame)


def media_duration_frame_range(group: pd.DataFrame, fps: float) -> tuple[int, int]:
    frame_count = first_positive_integer_from_columns(group, FRAME_COUNT_COLUMNS)
    if frame_count is not None:
        return 0, max(0, frame_count)

    duration = first_positive_number_from_columns(group, MEDIA_DURATION_COLUMNS)
    if duration is not None:
        return 0, max(0, int(math.ceil(duration * fps - EPSILON)))

    max_stop = max_event_stop(group)
    return 0, max(0, int(math.floor(max_stop * fps + EPSILON)) + 1)


def selected_time_bounds(parameters: dict = None) -> tuple[float | None, float | None]:
    if not parameters:
        return None, None
    start_time = numeric_value(parameters.get("start time"))
    stop_time = numeric_value(parameters.get("end time"))
    return start_time, stop_time


def first_positive_integer_from_columns(group: pd.DataFrame, columns: tuple[str, ...]) -> int | None:
    for column in columns:
        if column not in group.columns:
            continue
        value = first_positive_number(group[column])
        if value is not None:
            return int(value)
    return None


def first_positive_number_from_columns(group: pd.DataFrame, columns: tuple[str, ...]) -> float | None:
    for column in columns:
        if column not in group.columns:
            continue
        value = first_positive_number(group[column])
        if value is not None:
            return value
    return None


def first_positive_number(values) -> float | None:
    for value in values:
        numeric = numeric_value(value)
        if numeric is not None and numeric > 0:
            return numeric
    return None


def numeric_value(value: object) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(numeric):
        return None
    return numeric


def max_event_stop(group: pd.DataFrame) -> float:
    values = pd.to_numeric(group["Stop (s)"], errors="coerce").dropna()
    if values.empty:
        return 0.0
    return max(0.0, float(values.max()))
