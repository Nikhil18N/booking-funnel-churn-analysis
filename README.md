# Booking Funnel & Churn Analysis

Professional, reproducible analysis of a simulated travel booking funnel.

## Overview

This repository generates a realistic 5-stage booking funnel dataset, performs
stage-by-stage drop-off analysis and cohort-based churn/retention analysis,
and exports Google Sheets-ready CSVs and visualization PNGs.

Key outputs are written to `data/` and `sheets/` and include the raw
event dataset, funnel summaries, cohort retention matrices, churn
summaries, and charts.

## Contents

- `python/funnel_churn_analysis.py` — main analysis script (data generation, analysis, charts)
- `data/` — generated event and summary CSVs (ignored from VCS by default)
- `sheets/` — CSVs and charts prepared for Google Sheets export
- `outputs/` — optional analysis outputs (not tracked)

## Quick Start

1. Create a virtual environment (recommended):

	```bash
	python -m venv .venv
	.venv\Scripts\activate    # Windows
	source .venv/bin/activate  # macOS / Linux
	```

2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Run the analysis (writes CSVs and charts):

	```bash
	python python/funnel_churn_analysis.py
	```

4. Inspect outputs in `data/` and `sheets/` (CSV + `sheets/charts` PNGs).

## Dependencies

See `requirements.txt` for pinned runtime dependencies. Primary libraries:
- `pandas`, `numpy`, `matplotlib`, `seaborn`.

## Files produced

- `data/funnel_events.csv` — raw simulated event-level data
- `data/funnel_summary.csv` — stage-by-stage counts and drop-offs
- `data/cohort_retention.csv` — retention table by acquisition month
- `data/churn_summary.csv` — 30/60/90-day retention summary
- `sheets/*` — Google Sheets-ready CSVs and `sheets/charts/*.png` images

## Reproducibility

The data generation uses fixed random seeds for repeatable results. To re-run
the simulation with a new seed, edit the seed values in
`python/funnel_churn_analysis.py` near the top of the file.

## Contributing

Contributions are welcome — see `CONTRIBUTING.md` for the repo's
contribution guidelines.

## License

This project is licensed under the MIT License. See `LICENSE`.

## Contact

Open an issue or pull request on GitHub for questions, improvements, or
requests for additional analyses.