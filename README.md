# BORIS Plugins

Python plugins for analysing and exporting data from
[BORIS](https://www.boris.unito.it/), the Behavior Observation Research
Interactive Software.

These plugins are intended to be loaded by BORIS and run on the BORIS events
dataframe. Most plugins return a pandas dataframe that BORIS can display or
export; export plugins write files such as JSON or Praat TextGrid.

## Installation

Refer to the [BORIS user guide](https://www.boris.unito.it/user_guide/).


If you want to modifiy/improve a plugin download and save it in your personal BORIS plugins directory.


## Requirements

The plugins run inside the Python environment used by BORIS.



## Current Plugins

### Analysis

| File | BORIS plugin name | Output |
| --- | --- | --- |
| `time_budget.py` | Time budget | Counts, total duration, duration statistics, inter-event intervals, and percent of subject observation duration by subject and behavior. |
| `time_budget_hours.py` | Time budget (hours) | Time budget summary with durations expressed in hours. |
| `number_of_occurences.py` | Number of occurences of behaviors | Count of behavior occurrences by subject and behavior. |
| `number_of_occurences_by_independent_variable.py` | Number of occurences of behaviors by subject by independent_variable | Count of behavior occurrences grouped by independent variable, subject, and behavior. |
| `latency.py` | Behavior latency | Detail and summary tables for latency between behavior pairs by observation and subject. |
| `list_of_dataframe_columns.py` | List of dataframe columns | Diagnostic table listing the columns present in the BORIS dataframe. |

### Inter-rater reliability

| File | BORIS plugin name | Notes |
| --- | --- | --- |
| `irr_cohen_kappa.py` | Inter Rater Reliability - Unweighted Cohen's Kappa NEW | Pairwise unweighted Cohen's kappa between observations. Supports duration and instantaneous events. |
| `irr_weighted_cohen_kappa.py` | Inter Rater Reliability - Weighted Cohen's Kappa NEW | Pairwise Cohen's kappa weighted by duration; instantaneous events receive a user-selected fixed weight. |
| `irr_cohen_kappa_with_modifiers.py` | Inter Rater Reliability - Unweighted Cohen's Kappa with modifiers NEW | Unweighted Cohen's kappa with BORIS modifier values included in the compared category labels. |
| `irr_weighted_cohen_kappa_with_modifiers.py` | Inter Rater Reliability - Weighted Cohen's Kappa with modifiers NEW | Duration-weighted Cohen's kappa with modifier values included in the compared category labels. |

The kappa plugins compare BORIS observations pairwise. They use `Observation id`
as the observer/comparison unit and encode categories from subject and behavior;
the modifier variants also include BORIS modifier columns.

### Export

| File | BORIS plugin name | Output |
| --- | --- | --- |
| `export_to_praat_textgrid.py` | Export events as Praat TextGrid (subject-behavior tiers) | Writes one Praat `.TextGrid` file per observation, with one tier per subject/behavior pair. |
| `export_to_feral.py` | Export observations to FERAL | Writes a FERAL-compatible JSON file with behavior classes, per-frame labels, and train/validation/test/inference splits. |

## Older Versioned Copies

The following files are kept as versioned snapshots:

- `irr_cohen_kappa-0.0.3.py`
- `irr_cohen_kappa_with_modifiers-0.0.3.py`
- `irr_weighted_cohen_kappa-0.0.4.py`
- `irr_weighted_cohen_kappa_with_modifiers-0.0.3.py`

Use the unversioned files above unless you specifically need to reproduce
results from one of these older plugin versions.

## Expected BORIS Data



## Development Notes

Each plugin exposes a `run(...)` function that BORIS calls with the selected
events dataframe, and in some cases the project data or selected parameters.

When adding or updating a plugin:

- Keep `__plugin_name__`, `__version__`, `__version_date__`, and `__author__`
  up to date.
- Return a pandas dataframe for tabular analysis results when possible.
- Return a short string message for export plugins or user-facing errors.


## License

This project is distributed under the GNU General Public License v3.0. See
[`LICENSE`](LICENSE) for the full license text.
