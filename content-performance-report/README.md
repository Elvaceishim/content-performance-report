# Content Performance Report

This CLI combines monthly CSV exports into a single performance summary. It lives next to the sample data so you can run it directly from this folder.

## Basic usage

Activate your virtualenv (optional) and run:

```
python3 content_report.py
```

With no flags the tool reads the `content_data/` folder and prints:
- overall totals
- channel-level rollups
- top posts sorted by views and CTR

## Helpful options

```
python3 content_report.py --start 2025-01-01 --end 2025-12-31
python3 content_report.py --channel LinkedIn
python3 content_report.py --top 3 --min-impr 500
python3 content_report.py --save
```

Flags can be mixed and matched, for example:

```
python3 content_report.py --start 2025-01-01 --end 2025-12-31 --top 3 --min-impr 500 --save
```

When `--save` is present the script writes CSV/JSON outputs to the working directory.

## Working from another directory

The data directory is detected relative to this script by default, so you can also run it from elsewhere:

```
python3 content-performance-report/content_report.py --channel Instagram --top 10
```

If you need to read a different folder, pass `--path /path/to/your/csvs`.
