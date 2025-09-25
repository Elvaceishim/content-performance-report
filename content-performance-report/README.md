# Content Performance Report

Generate consolidated performance metrics from monthly CSV exports so you can compare channels and spotlight top-performing content.

## What It Does
This CLI merges CSV rows from a folder (defaults to `content_data/` next to the script), normalizes dates and numeric fields, then prints channel rollups plus leaderboards filtered by your criteria.

## CSV Format
- `title`: post headline or identifier (required)
- `date`: publish date; supports `YYYY-MM-DD`, `DD/MM/YYYY`, or `MM/DD/YYYY`
- `channel`: distribution channel name (required)
- `views`: integer view count (required)
- `clicks`: integer click count (required)
- `impressions`: integer impression count (required)
- `url`: canonical URL for deduping (optional but recommended)

## Quickstart Commands
```
python3 content_report.py
python3 content_report.py --start 2025-01-01 --end 2025-12-31 --top 3 --min-impr 500 --save
python3 content_report.py --channel LinkedIn --top 3
python3 content-performance-report/content_report.py --channel Instagram --top 10
```

## CLI Flags
- `--path PATH` read CSVs from another folder (defaults to this script's `content_data/`)
- `--start DATE` include rows on/after a date
- `--end DATE` include rows on/before a date
- `--channel NAME` filter results to a single channel (case-insensitive)
- `--top N` limit both leaderboards to the first *N* posts (default 5)
- `--min-impr NUM` require at least this many impressions for a post to appear (default 100)
- `--save` write CSV/JSON outputs to the current working directory

## Sample Output
```
=== Overall ===
{'posts': 4, 'views': 10750, 'clicks': 771, 'impressions': 34400, 'ctr_pct': 2.24}

Channel summary
Youtube | 1 | 4800 | 390 | 15000 | 2.6
Linkedin | 2 | 4050 | 233 | 13300 | 1.75
Medium | 1 | 1900 | 148 | 6100 | 2.43

Top 3 posts by views (min_impr=500)
AI Tools for Writers | Youtube | 4800 | 390 | 15000 | 2.6
Intro to Python | Linkedin | 2100 | 150 | 7200 | 2.08
Regex Cheatsheet | Linkedin | 1950 | 83 | 6100 | 1.36
```

## Privacy Note
The script only reads CSV files you point it to and writes optional reports to your local working directory—no data is transmitted anywhere.
